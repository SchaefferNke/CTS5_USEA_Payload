#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	silicate.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2023-11-06"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import time
import datetime
import zipfile
import traceback

# Project libraries
from system.io_lib import DriverIOOutput, DriverIOInput
from system.serial_lib import DriverSerial
from system.timer_lib import DriverTimer
from system.share_lib import DataShare, get_navigation, get_profile
from system.trace_lib import trace_log
from system.const import *

# Versioning
SILICATE_VERSION = "v1.0.0"


# Compute NMEA checksum (receive)
def nmea_checksum_check(frame: bytes) -> bool:
	"""
		Check the checksum value of a received frame

		Parameters:
			- frame (bytes): bytes read from the serial port

		Returns:
			- bool: True if the frame is correct
	"""
	if chr(frame[-3]) != "*":
		return False
	checksum = 0
	for c in frame[0:-3]:
		checksum ^= c
	if int(frame[-2:], 16) == checksum:
		return True
	return False


# Compute NMEA checksum (ascii transmit)
def nmea_checksum_compute_ascii(frame: str, count: int) -> int:
	"""
		Compute the checksum of a frame to send

		Parameters:
			- frame (str): frame to send
			- count (int): number of bytes to send

		Returns:
			- int: computed checksum
	"""
	checksum = 0
	for c in frame[0:count]:
		checksum ^= ord(c)
	return checksum


# Class definition
class DriverSilicate:
	"""
		DriverSilicate class: manage acquisition and communication with sensor
	"""

	# Create resource
	def __init__(self):
		# Manager
		self._step = USEA_PAYLOAD_STEP_SURFACE
		self._io_power = DriverIOOutput("GPIO_3_20")
		self._io_alarm = DriverIOInput("GPIO_2_0")
		self._serial = DriverSerial("COM_5", 57600, len("DATA,xxx,xxxx,*CS\r\n") + 512, 0.15)
		self._timer = DriverTimer(path, "silicate")
		self._share_step = DataShare("silicate_step")

	# Get version
	@staticmethod
	def get_version(self) -> str: return SILICATE_VERSION

	# Send frame over EMAP link
	def send_ascii(self, trace_path: str, frame: str):
		"""
			Send a frame on the serial port

			Parameters:
				- trace_path (str): ...
				- frame (str): frame to send
		"""
		checksum = nmea_checksum_compute_ascii(frame, len(frame))
		frame_ascii = "$" + frame + "*%0*X" % (2, checksum)
		time.sleep(0.05)
		self._serial.write(frame_ascii.encode("ascii"))
		trace_log(trace_path, "SILICATE > Tx=" + frame_ascii)

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Scheduler
		manager(self)


# EMAP
def emap(self):
	"""
		Running task
	"""

	global path
	file_name = ""
	index_cpt = 0

	# Start timer
	self._timer.start_one_shot(60.0)

	# Open serial port
	if self._serial.open():
		try:

			# Timestamp
			now = datetime.datetime.now()
			# Send request
			self.send_ascii(path, now.strftime("GPS,20%y%m%d,%H%M%S"))

			# Loop
			while not self._timer.is_tick():

				# New character ?
				if self._serial.in_waiting() == 0:
					time.sleep(0.1)
					continue
				# Wait start of frame
				if self._serial.read(1).decode() != "$":
					continue

				# Read frame
				frame_rx = self._serial.read(len("DATA,xxx,xxxx,*CS\r\n") + 512)
				# End of line sequence (optional)
				if chr(frame_rx[-2]) == "\r" and chr(frame_rx[-1]) == "\n":
					frame_rx = frame_rx[0:-2]
				elif chr(frame_rx[-1]) == "\n":
					frame_rx = frame_rx[0:-1]
				elif chr(frame_rx[-1]) == "\r":
					frame_rx = frame_rx[0:-1]
				# Verify checksum
				if not nmea_checksum_check(frame_rx):
					# Print
					trace_log(path, "SILICATE > [CHECKSUM]")
					# Continue
					continue
				# Extract data
				frame_data = frame_rx[0:-3]
				frame_string = frame_rx.decode("ascii", "ignore")
				data_string = frame_data.decode("ascii", "ignore")

				# GPSACK processing
				if "GPSACK" in frame_string[0:6]:
					# Print
					trace_log(path, "SILICATE > Rx=$" + frame_string)
					# Send request
					self.send_ascii(path, "LIST")

				# LISTACK processing
				elif "LISTACK," in frame_string[0:8]:
					# Print
					trace_log(path, "SILICATE > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Request file
					if int(split[1]) > 0:
						# Filename
						file_name = path + "payload/" + split[2]
						# Reply
						self.send_ascii(path, "GET," + split[2] + ",531")
					# Exit
					else:
						return

				# GETACK processing
				elif "GETACK" in frame_string[0:6]:
					# Print
					trace_log(path, "SILICATE > Rx=$" + frame_string)
					# Remove file
					if os.path.isfile(file_name):
						os.remove(file_name)
					# Initialize block
					index_cpt = 1
					# Reply
					self.send_ascii(path, "GETDATA")

				# DATA processing
				elif "DATA," in frame_string[0:5]:
					# Parse
					split = data_string.split(",")
					# Print
					if int(split[2]) > 0:
						trace_log(path, "SILICATE > Rx=$" + split[0] + "," + split[1] + "," + split[2] + ",[...]*" + frame_string[-2:])
					else:
						trace_log(path, "SILICATE > Rx=$" + split[0] + "," + split[1] + ",0*" + frame_string[-2:])
					# Check size
					if split[2] == "0":
						# Reply
						self.send_ascii(path, "DATAACK," + split[1])
					# Check index
					elif index_cpt == int(split[1]):
						# Next block
						index_cpt += 1
						# Write into file
						file_handle = open(file_name, "ab+")
						file_handle.write(frame_data[len("DATA,,,") + len(split[1]) + len(split[2]):])
						file_handle.close()
						# Reply
						self.send_ascii(path, "DATAACK," + split[1])
					# Error
					else:
						self.send_ascii(path, "DATANACK")

				# EOF processing
				elif "EOF" in frame_string[0:3]:
					# Print
					trace_log(path, "SILICATE > Rx=$" + frame_string)
					# Send request
					self.send_ascii(path, "LIST")

				# Unknown command
				else:
					# Print
					trace_log(path, "SILICATE > Rx=" + frame_string + " [UNDEFINED]")

		# Error
		except Exception as err:
			# Trace
			print(err)
			print(traceback.format_exc())
			# Trace
			trace_log(path, "SILICATE > [ERROR]")

	# Close serial port
	self._serial.close()


# Compression
def compress():
	"""
		Compress the data files
		"""
	# Create names
	zip_src_name = path + "payload/"
	zip_tmp_name = path + "temp/" + get_profile(path) + "_payload.zip"
	zip_dst_name = path + "payload/" + get_profile(path) + "_payload.zip"
	# No file to compress
	if not os.listdir(zip_src_name):
		return
	# Remove src archive
	if os.path.isfile(zip_tmp_name):
		os.remove(zip_tmp_name)
	# Remove dst archive
	if os.path.isfile(zip_dst_name):
		os.remove(zip_dst_name)
	# Create archive
	zip_file = zipfile.ZipFile(zip_tmp_name, "w")
	# For files in folder
	while True:
		# Scan directory
		if not os.listdir(zip_src_name):
			break
		# File name
		file_name = os.listdir(zip_src_name)[0]
		# Add file
		zip_file.write(zip_src_name + file_name, file_name, compress_type=zipfile.ZIP_DEFLATED)
		# Remove file
		os.remove(zip_src_name + file_name)
	# Close archive
	zip_file.close()
	# Move archive
	os.rename(zip_tmp_name, zip_dst_name)


# Create resources
path = "./"
silicate_driver = DriverSilicate()


# Manager
def manager(self):
	global path

	# Trace
	trace_log(path, "SILICATE > Activate")
	# Share step
	self._share_step.write(self._step)

	# Loop
	try:
		while True:

			# Read resource
			navigation = get_navigation(path)

			# Wait
			if self._step == USEA_PAYLOAD_STEP_IDLE:
				# Parking step
				if navigation == USEA_NAVIGATION_STATE_PARK:
					# Print
					trace_log(path, "SILICATE > Start acquisition")
					# Power-on
					self._io_power.set_on()
					# Start recording
					self._step = USEA_PAYLOAD_STEP_RECORD
					# Share step
					self._share_step.write(self._step)
				# Wait
				else:
					time.sleep(0.1)

			# Record
			elif self._step == USEA_PAYLOAD_STEP_RECORD:
				# Ascent
				if navigation == USEA_NAVIGATION_STATE_ASCENT:
					# Print
					trace_log(path, "SILICATE > Stop acquisition")
					# Power-on
					self._io_power.set_off()
					# Stop recording
					self._step = USEA_PAYLOAD_STEP_SURFACE
					# Share step
					self._share_step.write(self._step)
				# Wait
				else:
					time.sleep(0.1)

			# Surface
			elif self._step == USEA_PAYLOAD_STEP_SURFACE:
				# Treatment step
				if navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Print
					trace_log(path, "SILICATE > Start download")
					# Download files
					emap(self)
					# Print
					trace_log(path, "SILICATE > Stop download")
					# Idle
					self._step = USEA_PAYLOAD_STEP_IDLE
					# Share step
					self._share_step.write(self._step)
					# Compress files
					compress()

				# Wait
				else:
					time.sleep(0.1)

			# Other
			else:
				time.sleep(0.1)

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log(path, "SILICATE > [ERROR]")


# Test function
if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")
	path = "../"
	# Allocate resource
	silicate = DriverSilicate()
	# Run
	silicate.run()

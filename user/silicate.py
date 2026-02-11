#!/bin/python
# -*- coding: utf-8 -*-
"""
	silicate.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-02-11"
__version__ = "1.0.1"

# Standard libraries
import os
import sys
import time
import datetime
import traceback

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.io_lib import DriverIOOutput, DriverIOInput
from system.serial_lib import DriverSerial
from system.timer_lib import DriverTimer
from system.share_lib import DataShare, get_navigation
from system.trace_lib import trace_log
from system.const import *

# Versioning
SILICATE_VERSION = "1.0.1"


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
	def __init__(self, user_index: int):
		# Manager
		self._user_index = user_index
		self._step = USEA_USER_STEP_IDLE
		self._io_power = DriverIOOutput("GPIO_3_20")
		self._io_alarm = DriverIOInput("GPIO_5_5")
		self._serial = DriverSerial("COM_5", 115200, 0.15)
		self._timer = DriverTimer("silicate")
		if user_index == 0:
			self._share_step = DataShare("user_step")
		else:
			self._share_step = DataShare(f"user{user_index}_step")

	# Get version
	# noinspection PyMethodMayBeStatic
	def get_version(self) -> str: return SILICATE_VERSION

	# Send frame over EMAP link
	def send_ascii(self, frame: str):
		"""
			Send a frame on the serial port

			Parameters:
				- frame (str): frame to send
		"""
		checksum = nmea_checksum_compute_ascii(frame, len(frame))
		frame_ascii = "$" + frame + "*%0*X" % (2, checksum)
		time.sleep(0.05)
		self._serial.write(frame_ascii.encode("ascii"))
		trace_log("SILICATE > Tx=" + frame_ascii)

	# Test sensor
	def test(self) -> str:
		"""
			Test process

			Returns:
				- str: result string (eg: "silicate: ok", silicate: ok/error format)
		"""
		# Download files
		emap(self)
		# Reply
		return "silicate: ok"

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

	file_name = ""
	index_cpt = 0

	# Start timer
	self._timer.start_one_shot(120.0)

	# Wait
	time.sleep(0.25)
	# Trace
	trace_log("SILICATE > Enable")
	# Activate UART
	self._io_power.set_on()
	# Wait
	time.sleep(2.5)

	# Open serial port
	if self._serial.open():
		try:

			# Timestamp
			now = datetime.datetime.now()
			# Send request
			self.send_ascii(now.strftime("GPS,20%y%m%d,%H%M%S"))

			# Loop
			while not self._timer.is_tick():

				# New character ?
				if self._serial.in_waiting() == 0:
					time.sleep(0.1)
					continue
				# Wait start of frame
				try:
					# Read char
					start_char = self._serial.read(1).decode()
					# Test start of frame
					if start_char != "$":
						continue
				# Bad character
				except UnicodeDecodeError:
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
					trace_log("SILICATE > [CHECKSUM]")
					# Continue
					continue
				# Extract data
				frame_data = frame_rx[0:-3]
				frame_string = frame_rx.decode("ascii", "ignore")
				data_string = frame_data.decode("ascii", "ignore")

				# GPSACK processing
				if "GPSACK" in frame_string[0:6]:
					# Print
					trace_log("SILICATE > Rx=$" + frame_string)
					# Send request
					self.send_ascii("LIST")

				# LISTACK processing
				elif "LISTACK," in frame_string[0:8]:
					# Print
					trace_log("SILICATE > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Request file
					if int(split[1]) > 0:
						# Filename
						file_name = "payload/" + split[2]
						# Reply
						self.send_ascii("GET," + split[2] + ",531")
					# Exit
					else:
						break

				# GETACK processing
				elif "GETACK" in frame_string[0:6]:
					# Print
					trace_log("SILICATE > Rx=$" + frame_string)
					# Remove file
					if os.path.exists(file_name):
						os.remove(file_name)
					# Initialize block
					index_cpt = 1
					# Reply
					self.send_ascii("GETDATA")

				# DATA processing
				elif "DATA," in frame_string[0:5]:
					# Parse
					split = data_string.split(",")
					# Print
					if int(split[2]) > 0:
						trace_log("SILICATE > Rx=$" + split[0] + "," + split[1] + "," + split[2] + ",[...]*" + frame_string[-2:])
					else:
						trace_log("SILICATE > Rx=$" + split[0] + "," + split[1] + ",0*" + frame_string[-2:])
					# Check size
					if split[2] == "0":
						# Reply
						self.send_ascii("DATAACK," + split[1])
					# Check index
					elif index_cpt == int(split[1]):
						# Next block
						index_cpt += 1
						# Write into file
						file_handle = open(file_name, "ab+")
						file_handle.write(frame_data[len("DATA,,,") + len(split[1]) + len(split[2]):])
						file_handle.close()
						# Reply
						self.send_ascii("DATAACK," + split[1])
					# Error
					else:
						self.send_ascii("DATANACK")

				# EOF processing
				elif "EOF" in frame_string[0:3]:
					# Print
					trace_log("SILICATE > Rx=$" + frame_string)
					# Send request
					self.send_ascii("LIST")

				# Unknown command
				else:
					# Print
					trace_log("SILICATE > Rx=" + frame_string + " [UNDEFINED]")

		# Error
		except Exception as err:
			# Trace
			print(err)
			print(traceback.format_exc())
			# Trace
			trace_log("SILICATE > [ERROR]")

	# Close serial port
	self._serial.close()
	# Wait
	time.sleep(0.25)
	# Trace
	trace_log("SILICATE > Disable")
	# Deactivate UART
	self._io_power.set_off()
	# Wait
	time.sleep(2.5)


# Create resources
silicate_driver = DriverSilicate(0)


# Manager
def manager(self):

	# Trace
	trace_log("SILICATE > Activate")
	# Share step
	self._share_step.write(self._step)

	# Sleep
	self._io_power.set_off()

	# Loop
	while True:
		try:

			# Read resource
			navigation = get_navigation()

			# Wait
			if self._step == USEA_USER_STEP_IDLE:
				# Parking step
				if navigation == USEA_NAVIGATION_STATE_PARK:
					# Wait
					time.sleep(1.0)
					# Print
					trace_log("SILICATE > Start acquisition")
					# Awake
					self._io_power.set_on()
					# Start recording
					self._step = USEA_USER_STEP_RECORD
					# Share step
					self._share_step.write(self._step)
				# Wait
				else:
					time.sleep(0.1)

			# Record
			elif self._step == USEA_USER_STEP_RECORD:
				# Ascent
				if navigation == USEA_NAVIGATION_STATE_ASCENT:
					# Wait
					time.sleep(1.0)
					# Print
					trace_log("SILICATE > Stop acquisition")
					# Sleep
					self._io_power.set_off()
					# Stop recording
					self._step = USEA_USER_STEP_SURFACE
					# Share step
					self._share_step.write(self._step)
				# Wait
				else:
					time.sleep(0.1)

			# Surface
			elif self._step == USEA_USER_STEP_SURFACE:
				# Treatment step
				if navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Wait
					time.sleep(1.0)
					# Print
					trace_log("SILICATE > Data download")
					# Download files
					emap(self)
					# Print
					trace_log("SILICATE > Data compression")
					# Print
					trace_log("SILICATE > Data ready")
					# Idle
					self._step = USEA_USER_STEP_IDLE
					# Share step
					self._share_step.write(self._step)

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
			trace_log("SILICATE > [ERROR]")


# Test function
if __name__ == "__main__":
	# Run
	silicate_driver.run()

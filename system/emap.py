#!/bin/python
# -*- coding: utf-8 -*-
"""
	emap.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-06-04"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import time
import datetime
import zipfile
import traceback

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.system_lib import system_driver
from system.rtc import rtc_driver
from system.serial_lib import DriverSerial
from system.timer_lib import DriverTimer
from system.share_lib import DataShare, FileShare
from system.config import user_driver
from system.technical import technical_driver
from system.trace_lib import trace_log
from system.const import *

# EMAP wake-up duration
EMAP_WAKEUP_DURATION = 20.0


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


# Compute NMEA checksum (binary transmit)
def nmea_checksum_compute_binary(frame: str, content: bytes, count_frame: int, count_content: int) -> int:
	"""
		Compute the checksum of a frame to send

		Parameters:
			- frame (str): frame to send
			- content (bytes): content to send
			- count_frame (int): number of frame bytes to send
			- count_content (int): number of content bytes to send

		Returns:
			- int: computed checksum
	"""
	checksum = 0
	for c in frame[0:count_frame]:
		checksum ^= ord(c)
	for c in content[0:count_content]:
		checksum ^= c
	return checksum


# Class definition
class DriverEMAP:
	"""
		DriverEMAP class: manage communication with APMT navigation board
	"""

	# Create resource
	def __init__(self):
		# Manager
		if not os.name == "nt":
			self._serial = DriverSerial("COM_8", 57600, len("DATA,xxx,xxxx,*CS\r\n") + 512, 0.15)
		else:
			self._serial = DriverSerial("COM_1", 57600, len("DATA,xxx,xxxx,*CS\r\n") + 512, 0.15)
		self._timer = DriverTimer("emap")
		self._payload_step = DataShare("payload_step")
		self._payload = user_driver
		# Status
		share = FileShare("profile.txt")
		share.read()
		self._profile = share.content.string
		if self._profile == "?":
			self._profile = "xxx_xx"
		share = FileShare("pressure.txt")
		share.read()
		self._pressure = share.content.string
		if self._pressure == "?":
			self._pressure = "0.00"
		share = FileShare("navigation.txt")
		share.read()
		self._navigation = share.content.string
		if self._navigation == "?":
			self._navigation = "XX"

	# Status json
	def status_json(self) -> object:
		"""
			Save json information

			Returns:
				- object: json object
		"""
		# Navigation stage
		if self._navigation == "NA":
			navigation = "BUOYANCY_DECREASE"
		elif self._navigation == "NB":
			navigation = "DESCENT"
		elif self._navigation == "NC":
			navigation = "PARK"
		elif self._navigation == "ND":
			navigation = "DEEP_DESCENT"
		elif self._navigation == "NE":
			navigation = "DEEP_PARK"
		elif self._navigation == "NF":
			navigation = "ASCENT"
		elif self._navigation == "NG":
			navigation = "SUB_SURFACE"
		elif self._navigation == "NH":
			navigation = "BUOYANCY_INCREASE"
		elif self._navigation == "NI":
			navigation = "RESCUE"
		elif self._navigation == "NJ":
			navigation = "ASCENT"
		elif self._navigation == "NK":
			navigation = "ASCENT_SLOWLY"
		elif self._navigation == "NL":
			navigation = "ASCENT_RESUME"
		elif self._navigation == "SB":
			navigation = "GPS"
		elif self._navigation == "SC":
			navigation = "RUDICS"
		elif self._navigation == "SF":
			navigation = "SURFACE_ACQUISITION"
		elif self._navigation == "TC":
			navigation = "DATA_PROCESSING"
		elif self._navigation == "FN":
			navigation = "END_OF_LIFE"
		else:
			navigation = "UNDEFINED"
		# Sleep
		if os.path.isfile("share/sleep.txt"):
			sleep = "Enabled"
		else:
			sleep = "Disabled"
		# User information
		user_info = FileShare("user.txt")
		user_info.read()
		# Save
		result = {
			"profile": self._profile,
			"navigation": navigation,
			"pressure": self._pressure,
			"boot count": technical_driver.boot_count(),
			"sleep": sleep,
			"user": user_info.content.string}
		# Result
		return result

	# Send frame over EMAP link
	def _send_ascii(self, frame: str):
		"""
			Send a frame on the serial port

			Parameters:
				- frame (str): frame to send
		"""
		checksum = nmea_checksum_compute_ascii(frame, len(frame))
		frame_ascii = "$" + frame + "*%0*X" % (2, checksum)
		time.sleep(0.05)
		self._serial.write(frame_ascii.encode("ascii"))
		trace_log("EMAP     > Tx=" + frame_ascii)

	# Send frame over EMAP link
	def _send_ascii_no_trace(self, frame: str):
		"""
			Send a frame on the serial port

			Parameters:
				- frame (str): frame to send
		"""
		checksum = nmea_checksum_compute_ascii(frame, len(frame))
		frame_ascii = "$" + frame + "*%0*X" % (2, checksum)
		time.sleep(0.05)
		self._serial.write(frame_ascii.encode("ascii"))

	def _send_binary(self, frame: str, content: bytes):
		"""
			Send a frame on the serial port (without data detail on debug)

			Parameters:
				- frame (str): frame to send
				- content (bytes): frame content
		"""
		checksum = nmea_checksum_compute_binary(frame, content, len(frame), len(content))
		frame_ascii = "$" + frame + "[...]" + "*%0*X" % (2, checksum)
		time.sleep(0.05)
		string = "$" + frame
		self._serial.write(string.encode("ascii"))
		self._serial.write(content)
		string = "*%0*X" % (2, checksum)
		self._serial.write(string.encode("ascii"))
		trace_log("EMAP     > Tx=" + frame_ascii)

	# Get time before next activity
	def get_time_before_activity(self) -> float:
		"""
			Get the time remaining before the next activity

			Returns:
				- float: time remaining before the next activity (sec)
		"""
		# Waiting for the next command
		if self._timer.remaining_time() > 0.0:
			return EMAP_WAKEUP_DURATION - self._timer.remaining_time()
		return 3600.0

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Scheduler
		manager(self)


# Create resources
emap_driver = DriverEMAP()


# Cleanup folder
def cleanup_folder(path_name: str):
	"""
		Cleanup a folder

		Parameters:
			- path_name (str): folder path
	"""
	# List files in folder
	files = os.listdir(path_name)
	# For all files
	for file_name in files:
		# Remove file
		os.remove(path_name + "/" + file_name)


# Logger extract
def logger_extract(size: int):
	"""
		Create extract of the logger file

		Parameters:
			- size (int): extract size (in bytes)
	"""
	# Create names
	log_src_name = "log/payload.log"
	log_dst_name = "temp/payload.log"
	zip_dst_name = "payload/payload_logger.zip"
	# Remove dst logger
	if os.path.isfile(log_dst_name):
		os.remove(log_dst_name)
	# Remove dst archive
	if os.path.isfile(zip_dst_name):
		os.remove(zip_dst_name)
	# Read extract
	file_src = open(log_src_name, "r")
	file_src.seek(0, os.SEEK_END)
	offset = file_src.tell()
	if offset < size:
		file_src.seek(0, os.SEEK_SET)
	else:
		file_src.seek(offset - size, os.SEEK_SET)
	content = file_src.read(size)
	file_src.close()
	# Write extract
	file_dst = open(log_dst_name, "w")
	file_dst.write(content)
	file_dst.close()
	# Create archive
	zip_file = zipfile.ZipFile(zip_dst_name, "w")
	# Add file
	zip_file.write(log_dst_name, "payload.log", compress_type=zipfile.ZIP_DEFLATED)
	# Close archive
	zip_file.close()
	# Remove file
	os.remove(log_dst_name)


# Update application
def update_application():
	"""
		Update the application
	"""
	# No update
	update = False
	# Create names
	zip_path = "./temp"
	zip_src_name = "payload_update.zip"
	# Clean directory
	existing_files = os.listdir(zip_path)
	# For all current files
	for existing_file_name in existing_files:
		# Except update file
		if not existing_file_name == zip_src_name:
			# Remove file
			os.remove(zip_path + "/" + existing_file_name)
	# Open archive
	zip_file = zipfile.ZipFile(zip_path + "/" + zip_src_name, "r")
	# Extract files
	zip_file.extractall(zip_path)
	# Close archive
	zip_file.close()
	# Remove archive
	os.remove(zip_path + "/" + zip_src_name)
	# List new files
	new_files = os.listdir(zip_path)
	# For all new files
	for new_file_name in new_files:
		# Parse
		split = new_file_name.split("#")
		# Destination
		if len(split) == 2:
			current_file_name = "./" + split[0] + "/" + split[1]
		else:
			current_file_name = "./" + new_file_name
		# Remove file
		if os.path.isfile(current_file_name):
			os.remove(current_file_name)
		# Move file
		os.rename(zip_path + "/" + new_file_name, current_file_name)
		# Wait
		time.sleep(0.025)
		# Trace
		trace_log("EMAP     > Update application file: " + current_file_name)
		# Update done
		update = True
	# Clean folder
	cleanup_folder(zip_path)
	# Wait
	time.sleep(1.0)
	# Apply changes
	if update:
		if not os.name == "nt":
			os._exit(0)


# Manager
def manager(self):
	"""
		Running task
	"""

	file_name = ""
	index_cpt = 0
	index_max = 0
	emap_buffer_size = 128

	# Trace
	trace_log("EMAP     > Activate")

	# Start timer
	self._timer.start_one_shot(EMAP_WAKEUP_DURATION)

	# Loop
	if self._serial.open():
		try:
			while True:

				# New character ?
				if self._serial.in_waiting() == 0:
					time.sleep(0.1)
					continue
				# Start timer
				self._timer.start_one_shot(EMAP_WAKEUP_DURATION)
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
					trace_log("EMAP     > [CHECKSUM]")
					# Continue
					continue
				# Extract data
				frame_data = frame_rx[0:-3]
				frame_string = frame_rx.decode("ascii", "ignore")
				data_string = frame_data.decode("ascii", "ignore")

				# VERSION processing
				if "VERSION" in frame_string[0:7]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Reply
					self._send_ascii("VERSIONACK," + USEA_VERSION + "-" + self._payload.get_version())

				# NAV processing
				elif "NAV," in frame_string[0:4]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Store information
					self._profile = f"{int(split[1]):03}_{int(split[2]):02}"
					# Share information
					share = FileShare("profile.txt")
					share.write(self._profile)
					# Reply
					self._send_ascii("NAVACK")

				# SEQ processing
				elif "SEQ," in frame_string[0:4]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Store information
					self._navigation = split[1]
					# Share information
					share = FileShare("navigation.txt")
					share.write(self._navigation)
					# Reply
					self._send_ascii("SEQACK")

				# CTRL processing
				elif "CTRL," in frame_string[0:5]:
					# Parse
					split = data_string.split(",")
					# Hydraulic action
					if split[1] != "NONE":
						# Share information
						share = FileShare("ctrl.txt")
						share.write(split[1])
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Reply
						self._send_ascii("CTRLACK")
					# No action
					else:
						# Reply
						self._send_ascii_no_trace("CTRLACK")
					# Store information
					self._pressure = split[2]
					# Share information
					share = FileShare("pressure.txt")
					share.write(self._pressure)

				# CTD processing
				elif "CTD," in frame_string[0:4]:
					# Print
					# trace_log("EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Share information
					share = FileShare("ctd.txt")
					share.write(split[1] + "," + split[2] + "," + split[3])
					# Store information
					self._pressure = f"{float(split[1]):.2f}"
					# Share information
					share = FileShare("pressure.txt")
					share.write(self._pressure)
					# No reply
					# self._send_ascii("CTDACK")

				# GPS processing
				elif "GPS," in frame_string[0:4]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Reply
					self._send_ascii("GPSACK")
					# Parse
					split = data_string.split(",")
					# Timestamp
					now = datetime.datetime.now()
					utc = now.replace(
						year=2000 + int(split[1][2:4]),
						month=int(split[1][4:6]),
						day=int(split[1][6:8]),
						hour=int(split[2][0:2]),
						minute=int(split[2][2:4]),
						second=int(split[2][4:6]),
						microsecond=0)
					# Drift
					drift = (now - utc).total_seconds()
					# Share information
					share = FileShare("synchro.txt")
					share.write(f"{drift:.3f}")
					# Lock for other threads
					share.lock()
					# Synchronize system clock
					rtc_driver.synchronize(utc)
					# Unlock
					share.unlock()

				# PING processing
				elif "PING" in frame_string[0:4]:
					# Sensor processing
					if self._payload_step.read() == USEA_PAYLOAD_STEP_TREAT:
						continue
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Reply
					self._send_ascii("PINGACK")

				# COMMAND processing
				elif "COMMAND," in frame_string[0:8]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# User version
					if split[2] == "?payload-version":
						# Get version
						reply = "Version " + USEA_VERSION + "-" + self._payload.get_version()
						# Reply
						self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
					# Configuration
					elif split[2] == "?payload-configuration":
						# Acquire data
						reply = user_driver.source_code
						# Reply
						self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
					# Sensor test
					elif split[2] == "?payload-data":
						# Acquire data
						reply = self._payload.get_data()
						# Reply
						self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
					# Autotest
					elif split[2] == "!payload-autotest":
						# Test
						reply = "payload : ok\r\n" + self._payload.test()
						# Reply
						self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
					# Flush system
					elif split[2] == "!payload-cleanup":
						# Clean folders
						cleanup_folder("./config")
						cleanup_folder("./ctd")
						cleanup_folder("./log")
						cleanup_folder("./payload")
						cleanup_folder("./share")
						cleanup_folder("./temp")
						cleanup_folder("./trash")
						# Reply
						self._send_ascii("COMMANDACK,12,Command okay")
					# Update
					elif split[2] == "!update:payload_update.zip":
						# Check if update file exists
						if os.path.isfile("temp/payload_update.zip"):
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
							# Wait
							time.sleep(0.5)
							# Update
							update_application()
						# Error
						else:
							# Reply
							self._send_ascii("COMMANDACK,13,Command error")
					# Application reset
					elif split[2] == "!payload-reset":
						# Reply
						self._send_ascii("COMMANDACK,12,Command okay")
						# Delay
						time.sleep(0.5)
						# Restart
						system_driver.reboot()
					# Activate sleep mode
					elif split[2] == "!payload-sleep:1":
						# Save
						if not os.path.isfile("share/sleep.txt"):
							file_request = open("share/sleep.txt", "w")
							file_request.close()
						# Reply
						self._send_ascii("COMMANDACK,12,Command okay")
					# Deactivate sleep mode
					elif split[2] == "!payload-sleep:0":
						# Save
						if os.path.isfile("share/sleep.txt"):
							os.remove("share/sleep.txt")
						# Reply
						self._send_ascii("COMMANDACK,12,Command okay")
					# Logger request
					elif split[2] == "!payload-logger:1":
						# Test request
						if not os.path.isfile("temp/logger.txt"):
							file_request = open("temp/logger.txt", "w")
							file_request.close()
						# Reply
						self._send_ascii("COMMANDACK,12,Command okay")
					# Cancel logger request
					elif split[2] == "!payload-logger:0":
						# Save
						if os.path.isfile("temp/logger.txt"):
							os.remove("temp/logger.txt")
						# Reply
						self._send_ascii("COMMANDACK,12,Command okay")
					# Error
					else:
						self._send_ascii("COMMANDACK,15,Unknown command")

				# LIST processing
				elif "LIST" in frame_string[0:4]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Logger request
					if os.path.isfile("temp/logger.txt"):
						# Prepare logger extract
						logger_extract(64 * 1024)
						# Remove request
						os.remove("temp/logger.txt")
					# Scan directories
					file_list = os.listdir("payload/")
					# No file test
					no_file = True
					# Check file
					for list_name in file_list:
						# Get file size
						file_size = os.path.getsize("payload/" + list_name)
						# File size is correct
						if (file_size > 0) and (file_size < 131072):
							# Reply
							self._send_ascii("LISTACK,1," + list_name)
							# No file test
							no_file = False
							# Exit
							break
						# File size error
						else:
							# Move file
							os.rename("payload/" + list_name, "trash/" + list_name)
							# Next
							continue
					# No file
					if no_file:
						# Reply
						self._send_ascii("LISTACK,0")

				# GET processing
				elif "GET," in frame_string[0:4]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Filename
					file_name = "payload/" + split[1]
					# Buffer size
					emap_buffer_size = int(split[2]) - len("DATA,xxx,xxxx,*CS")
					# Reply
					if os.path.isfile(file_name):
						self._send_ascii("GETACK," + str(os.path.getsize(file_name)))
					else:
						self._send_ascii("GETNACK")

				# PUT processing
				elif "PUT," in frame_string[0:4]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Configuration file
					if split[1] == "payload.cfg":
						# Filename
						file_name = "config/payload.cfg"
						# Remove file
						if os.path.isfile(file_name):
							os.remove(file_name)
						# Initialize data block
						index_cpt = 1
						# Reply
						self._send_ascii("PUTACK,512")
					# Update file
					elif split[1] == "payload_update.zip":
						# Filename
						file_name = "temp/payload_update.zip"
						# Remove file
						if os.path.isfile(file_name):
							os.remove(file_name)
						# Initialize data block
						index_cpt = 1
						# Reply
						self._send_ascii("PUTACK,512")
					# Other
					else:
						# Reply
						self._send_ascii("PUTNACK")

				# DATA processing
				elif "DATA," in frame_string[0:5]:
					# Parse
					split = data_string.split(",")
					# Print
					if int(split[2]) > 0:
						trace_log("EMAP     > Rx=$" + split[0] + "," + split[1] + "," + split[2] + ",[...]*" + frame_string[-2:])
					else:
						trace_log("EMAP     > Rx=$" + split[0] + "," + split[1] + ",0*" + frame_string[-2:])
					# Check size
					if split[2] == "0":
						# Reply
						self._send_ascii("DATAACK," + split[1])
					# Check index
					elif index_cpt == int(split[1]):
						# Next block
						index_cpt += 1
						# Write into file
						file_handle = open(file_name, "ab+")
						file_handle.write(frame_data[len("DATA,,,") + len(split[1]) + len(split[2]):])
						file_handle.close()
						# Reply
						self._send_ascii("DATAACK," + split[1])
					# Error
					else:
						self._send_ascii("DATANACK")

				# GETDATA processing
				elif "GETDATA" in frame_string[0:7]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Initialize data blocks
					index_cpt = 1
					index_max = round(os.path.getsize(file_name) / emap_buffer_size) + 1
					# Read from file
					file_handle = open(file_name, "rb")
					content = file_handle.read(emap_buffer_size)
					file_handle.close()
					# Format
					frame = "DATA,1," + str(len(content)) + ","
					# Reply
					self._send_binary(frame, content)

				# DATAACK processing
				elif "DATAACK," in frame_string[0:8]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Last block
					if int(split[1]) > index_max:
						# Reply
						self._send_ascii("EOF")
						# Remove archive
						if os.path.isfile(file_name):
							os.remove(file_name)
					# New block
					elif int(split[1]) == index_cpt:
						# Read from file
						file_handle = open(file_name, "rb")
						file_handle.seek(index_cpt * emap_buffer_size)
						content = file_handle.read(emap_buffer_size)
						file_handle.close()
						# Next block
						index_cpt += 1
						# Reply
						if len(content) > 0:
							# Format
							frame = "DATA," + str(index_cpt) + "," + str(len(content)) + ","
							# Reply
							self._send_binary(frame, content)
						# Reply
						else:
							self._send_ascii("DATA," + str(index_cpt) + ",0")

				# DATAACK processing
				elif "DATANACK," in frame_string[0:9]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)

				# EOF processing
				elif "EOF" in frame_string[0:3]:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string)

				# Unknown command
				else:
					# Print
					trace_log("EMAP     > Rx=$" + frame_string + " [UNDEFINED]")

		# Error
		except Exception as err:
			# Trace
			print(err)
			print(traceback.format_exc())
			# Trace
			trace_log("EMAP     > [ERROR]")

	# Close serial port
	self._serial.close()


# Test function
if __name__ == "__main__":
	# Run
	emap_driver.run()

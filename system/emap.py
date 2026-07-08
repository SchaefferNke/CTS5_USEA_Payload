#!/bin/python
# -*- coding: utf-8 -*-
"""
	emap.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-07-03"
__version__ = "1.0.2"

# Standard libraries
import os
import sys
import time
import datetime
import zipfile
import shutil
import traceback
from checksumdir import dirhash

# Third-party libraries
import psutil

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.system_lib import system_driver
from system.rtc import rtc_driver
from system.serial_lib import DriverSerial
from system.timer_lib import DriverTimer
from system.share_lib import DataShare, FileShare, get_profile
from system.config import user_drivers
from system.technical import technical_driver
from system.trace_lib import trace_log
from system.const import *

# EMAP wake-up duration
EMAP_WAKEUP_DURATION = 20.0


# Compute NMEA checksum (receive)
def nmea_checksum_check(frame: bytes, star_index: int) -> bool:
	"""
		Check the checksum value of a received frame

		Parameters:
			- frame (bytes): bytes read from the serial port
			- star_index (int) : index of * character

		Returns:
			- bool: True if the frame is correct
	"""
	checksum = 0
	for c in frame[:star_index]:
		checksum ^= c
	try:
		cs_bytes = frame[star_index + 1:star_index + 3].decode("ascii")
	except UnicodeDecodeError:
		return False
	if not all(c in "0123456789ABCDEF" for c in cs_bytes):
		return False
	return int(cs_bytes, 16) == checksum


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


def compress_all_sensors():
	"""
	Compress all files from 'payload/' into a single archive.
	"""
	src = "payload/"
	tmp = "temp/" + get_profile() + "_payload.hex"
	dst = "payload/" + get_profile() + "_payload.hex"
	# Nothing to compress
	if not os.listdir(src):
		return
	# Remove old temporary file if exists
	if os.path.exists(tmp):
		os.remove(tmp)
	try:
		# Create new zip archive
		with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
			for file_name in os.listdir(src):
				file_path = os.path.join(src, file_name)
				# Exclude metadata and technical files
				if os.path.isfile(file_path) and\
					"payload.xml" not in file_name and\
					"payload.txt" not in file_name and\
					"payload.hex" not in file_name:
					zip_file.write(file_path, arcname=file_name)
					os.remove(file_path)
		# Move temp archive to final destination
		os.rename(tmp, dst)
		trace_log("EMAP     > Compressed files into " + get_profile() + "_payload.hex")
	# Error
	except Exception as e:
		trace_log(f"EMAP     > Compression error: {e}")


# Class definition
class DriverEMAP:
	"""
		DriverEMAP class: manage communication with APMT navigation board
	"""

	# Create resource
	def __init__(self):
		# Manager
		if not os.name == "nt":
			self._serial = DriverSerial("COM_8", 57600, 0.15)
		else:
			self._serial = DriverSerial("COM_1", 57600, 0.15)
		self._timer = DriverTimer("emap")
		self._tech_step = DataShare("tech_step")
		self._sleep_enable = False
		# User access
		self._user_step = []
		self._payloads = []
		for driver in user_drivers:
			if driver.user_index == 0:
				self._user_step.append(DataShare("user_step"))
			else:
				self._user_step.append(DataShare(f"user{driver.user_index}_step"))
			self._payloads.append(driver)
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
		# Heartbeat security
		self.heartbeat = time.monotonic()

	@staticmethod
	def _get_user_info_file(user_index: int) -> str:
		"""
		Return the user info filename depending on user index
		"""
		return "user.txt" if user_index == 0 else f"user{user_index}.txt"

	# Status json
	def status_json(self) -> object:
		"""
			Save json information

			Returns:
				- object: json object
		"""
		# Navigation stage
		navigation = USEA_NAVIGATION_MAP_2.get(self._navigation, "UNDEFINED")
		# Sleep
		if os.path.exists("share/sleep.txt"):
			sleep = "Enabled"
		else:
			sleep = "Disabled"
		# User information
		if not self._payloads:
			user_value = "?"
		else:
			users_info_with_state = []
			for driver in self._payloads:
				file_name = self._get_user_info_file(driver.user_index)
				user_share = FileShare(file_name)
				user_share.read()
				info = user_share.content.string.strip()
				state = USEA_USER_STATE_MAP.get(info, USEA_USER_STEP_IDLE)
				users_info_with_state.append((state, info))
			user_value = max(users_info_with_state, key=lambda x: x[0])[1]
		# Save
		result = {
			"profile": self._profile,
			"navigation": navigation,
			"pressure": self._pressure,
			"boot count": technical_driver.boot_count(),
			"sleep": sleep,
			"user": user_value}
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

	# Send frame over EMAP link (string content)
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

	# Send frame over EMAP link (binary content)
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

	# Activate/deactivate sleep mode management
	def sleep_mode_activation(self, enable: bool):
		"""
			Activate/deactivate the sleep management

			Parameters:
				- enable (bool): True or False
		"""
		# Store activation status
		self._sleep_enable = enable

	# Get time before next activity
	def get_time_before_activity(self) -> float:
		"""
			Get the time remaining before the next activity

			Returns:
				- float: time remaining before the next activity (sec)
		"""
		# Sleep available
		if not self._sleep_enable:
			return 0.0
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
	if os.path.exists(log_dst_name):
		os.remove(log_dst_name)
	# Remove dst archive
	if os.path.exists(zip_dst_name):
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


# Move files from SD card
def move_from_sd():
	"""
		Move files from SD card to payload folder
	"""
	# Read SD path
	sd_path = system_driver.disk2_path()
	# Check SD presence
	if not os.path.exists(sd_path):
		return
	# Try
	try:
		# List files in folder
		files = os.listdir(sd_path)
		# Check SD is empty
		if not files:
			return
		# For all files
		for file_name in files:
			# Ignore hidden or temporary files
			if file_name.startswith((".", "~")):
				continue
			# Create filenames
			src = sd_path + "/" + file_name
			dst = "payload/" + file_name
			# Ignore directories
			if not os.path.isfile(src):
				continue
			# Avoid overwrite
			if os.path.exists(dst):
				# Trace
				trace_log("EMAP     > Overwrite from microSD is forbidden: " + file_name)
				continue
			# Trace
			trace_log("EMAP     > Move file from microSD: " + file_name)
			# Move file
			shutil.move(src, dst)
			# Split if > 1 MB
			max_size = 1024 * 1024
			if os.path.getsize(dst) > max_size:
				base, ext = os.path.splitext(dst)
				i = 1
				with open(dst, "rb") as f:
					chunk = f.read(max_size)
					while chunk:
						with open(f"{base}#{i:02d}{ext}", "wb") as out:
							out.write(chunk)
						i += 1
						chunk = f.read(max_size)
				os.remove(dst)
	# Except
	except (OSError, shutil.Error):
		return


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
		if os.path.exists(current_file_name):
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
		if os.name != "nt":
			# noinspection PyProtectedMember,PyUnresolvedReferences
			os._exit(0)


# Compute source checksum
def source_checksum(user_files: list[str]) -> str:
	"""
	Compute the checksum of python source code

	Returns:
		- str: checksum string
	"""
	import shutil
	import os

	def calc_dir_checksum(temp_dir: str) -> str:
		chk = dirhash(temp_dir, "md5")
		return hex(int(chk[0:8], 16) ^ int(chk[8:16], 16) ^ int(chk[16:24], 16) ^ int(chk[24:32], 16))

	# Compute checksum "main"
	temp_main = "temp/chk_1/"
	shutil.rmtree(temp_main, ignore_errors=True)
	os.makedirs(temp_main)
	shutil.copyfile("main.py", temp_main + "main.py")
	str_1 = calc_dir_checksum(temp_main)
	shutil.rmtree(temp_main)
	# Compute checksum "system"
	temp_system = "temp/chk_2/"
	shutil.rmtree(temp_system, ignore_errors=True)
	os.makedirs(temp_system)
	for file_name in os.listdir("system/"):
		if file_name.endswith(".py"):
			shutil.copyfile("system/" + file_name, temp_system + file_name)
	str_2 = calc_dir_checksum(temp_system)
	shutil.rmtree(temp_system)
	# Compute checksum "user"
	temp_user = "temp/chk_3/"
	shutil.rmtree(temp_user, ignore_errors=True)
	os.makedirs(temp_user)
	valid_user_files = False
	for uf in user_files:
		if not uf:
			continue
		user_path = os.path.join("user", uf)
		if not os.path.isfile(user_path):
			continue
		shutil.copyfile(user_path, os.path.join(temp_user, uf))
		valid_user_files = True
	if valid_user_files:
		str_3 = calc_dir_checksum(temp_user)
	else:
		str_3 = "none"
	shutil.rmtree(temp_user)
	# Result
	return f"{str_1}-{str_2}-{str_3}"


# User process helper
def safe_user_call(name: str, func, default: str) -> str:
	# noinspection PyBroadException
	try:
		return func()
	except Exception:
		trace_log("EMAP     > User exception in " + name)
		trace_log(traceback.format_exc())
		return default


# Manager
def manager(self):
	"""
		Running task
	"""

	file_name = ""
	index_cpt = 0
	index_max = 0
	emap_buffer_size = 128
	rx_buffer = bytearray()
	last_frame_time = None

	# Trace
	trace_log("EMAP     > Activate")

	# Start timer
	self._timer.start_one_shot(EMAP_WAKEUP_DURATION)

	# Loop
	if self._serial.open():

		# Loop
		while True:

			# Heartbeat security
			self.heartbeat = time.monotonic()

			try:
				# New character is pending ?
				if self._serial.in_waiting() == 0:
					# Frame timeout
					if rx_buffer and last_frame_time is not None:
						if time.time() - last_frame_time > 0.5:
							trace_log("EMAP     > Rx=" + rx_buffer.decode("ascii", "ignore") + " [TIME-OUT]")
							rx_buffer.clear()
							last_frame_time = None
					time.sleep(0.05)
					continue
				# Start activity timer
				self._timer.start_one_shot(EMAP_WAKEUP_DURATION)
				# Read available bytes
				data = self._serial.read(self._serial.in_waiting())
				# Extend buffer only after seeing "$"
				dollar_index = data.find(b"$")
				if rx_buffer:
					rx_buffer.extend(data)
				elif dollar_index >= 0:
					rx_buffer.extend(data[dollar_index:])
					last_frame_time = time.time()
				# Overflow protection
				if len(rx_buffer) > len("$DATA,xxxx,xxxx,*CS") + 512:
					trace_log("EMAP     > [OVERFLOW]")
					rx_buffer.clear()
					continue
				# Remove any data before "$" except for DATA frame (binary content)
				start_index = rx_buffer.find(b"$")
				if start_index > 0 and not rx_buffer.startswith(b"$DATA,"):
					del rx_buffer[:start_index]

				# Treat frames in buffer
				while True:
					# Wait for candidate "$*CS"
					star_index = rx_buffer.find(b"*", 1)
					if star_index == -1 or star_index + 2 >= len(rx_buffer):
						break
					# Extract possible frame
					frame_rx = bytes(rx_buffer[1:star_index + 3])
					# Scan for valid checksum "CS"
					if not nmea_checksum_check(frame_rx, star_index - 1):
						# Remove frame except for DATA frame (binary content)
						if rx_buffer.startswith(b"$DATA,"):
							search_pos = star_index + 1
							found_valid = False
							while True:
								star_index = rx_buffer.find(b"*", search_pos)
								if star_index == -1 or star_index + 2 >= len(rx_buffer):
									break
								frame_rx = bytes(rx_buffer[1:star_index + 3])
								if nmea_checksum_check(frame_rx, star_index - 1):
									found_valid = True
									break
								search_pos = star_index + 1
							if not found_valid:
								break
						else:
							trace_log("EMAP     > Rx=$" + frame_rx.decode("ascii", "ignore") + " [CHECKSUM]")
							del rx_buffer[:star_index + 3]
							continue
					# Remove processed frame from buffer
					del rx_buffer[:star_index + 3]
					# Extract data
					frame_data = frame_rx[:-3]
					frame_string = frame_rx.decode("ascii", "ignore")
					data_string = frame_data.decode("ascii", "ignore")

					# VERSION processing
					if frame_string.startswith("VERSION"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Get version
						versions_str = "/".join(safe_user_call("get_version", p.get_version, "?") for p in self._payloads)
						# Reply
						self._send_ascii("VERSIONACK," + USEA_VERSION + "-" + versions_str)

					# NAV processing
					elif frame_string.startswith("NAV,"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Parse
						split = data_string.split(",")
						# Manage sleep activation
						if split[2] == "0":
							# Deactivate
							self.sleep_mode_activation(False)
						else:
							# Print
							trace_log("EMAP     > Sleep mode enabled")
							# Activate
							self.sleep_mode_activation(True)
						# Store information
						self._profile = f"{int(split[1]):03}_{int(split[2]):02}"
						# Share information
						share = FileShare("profile.txt")
						share.write(self._profile)
						# Reply
						self._send_ascii("NAVACK")

					# SEQ processing
					elif frame_string.startswith("SEQ,"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Parse
						split = data_string.split(",")
						# Store information
						self._navigation = split[1]
						# Share information
						share = FileShare("navigation.txt")
						share.write(self._navigation)
						# Parking stage
						if (
							(self._navigation == "NC") and
							(len(split) == 4)):
							# Share information
							share = FileShare("parking.txt")
							share.write(split[2]+","+split[3])
						# Reply
						self._send_ascii("SEQACK")

					# CTRL processing
					elif frame_string.startswith("CTRL,"):
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
					elif frame_string.startswith("CTD,"):
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
					elif frame_string.startswith("GPS,"):
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
					elif frame_string.startswith("PING"):
						# Sensor processing
						if (
							(self._tech_step.read() == USEA_TECHNICAL_STEP_TREAT) or
							any(user.read() == USEA_USER_STEP_TREAT for user in self._user_step)):
							continue
						# Compress
						compress_all_sensors()
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Reply
						self._send_ascii("PINGACK")

					# COMMAND processing
					elif frame_string.startswith("COMMAND,"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Parse
						split = data_string.split(",")
						# Version
						if split[2] == "?payload-version":
							# Get version
							reply = ("Version " + USEA_VERSION + "-" + "/".join(safe_user_call("get_version", p.get_version, "?") for p in self._payloads))
							# Reply
							self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
						# Checksum
						elif split[2] == "?payload-checksum":
							# Compute checksums
							user_files = []
							for p in self._payloads:
								if p.config_file:
									user_files.append(p.config_file)
								if p.source_code:
									user_files.append(p.source_code)
							reply = source_checksum(user_files)
							# Reply
							self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
						# Configuration
						elif split[2] == "?payload-configuration":
							# Acquire data
							reply = "/".join([p.source_code for p in self._payloads])
							# Reply
							self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
						# Sensor test
						elif split[2] == "?payload-data":
							# Acquire data
							if len(self._payloads) == 1:
								reply = safe_user_call("get_data", self._payloads[0].get_data, "no reply")
							else:
								values = []
								for i, p in enumerate(self._payloads, start=1):
									value = safe_user_call("get_data", p.get_data, "no reply")
									values.append(f"user{i}={value}")
								reply = ",".join(values)
							# Reply
							self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
						# Autotest
						elif split[2] == "!payload-autotest":
							# Test
							if len(self._payloads) == 1:
								reply = "payload : ok\r\n" + safe_user_call("test", self._payloads[0].test, "user    : error")
							else:
								lines = ["payload : ok"]
								for i, p in enumerate(self._payloads, start=1):
									lines.append(safe_user_call("test", p.test, "user    : error"))
								reply = "\r\n".join(lines)
							# Reply
							self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
						# Flush system
						elif split[2] == "!payload-cleanup-all":
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
						# Flush navigation
						elif split[2] == "!payload-cleanup-nav":
							# Clean navigation files
							share = FileShare("profile.txt")
							share.write("xxx_xx")
							share = FileShare("navigation.txt")
							share.write("?")
							share = FileShare("pressure.txt")
							share.write("0.00")
							if len(self._payloads) == 1:
								share = FileShare("user.txt")
								share.write("IDLE")
							else:
								for i, p in enumerate(self._payloads, start=1):
									share = FileShare(f"user{i}.txt")
									share.write("IDLE")
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
						# Update
						elif split[2] == "!update:payload_update.zip":
							# Check if update file exists
							if os.path.exists("temp/payload_update.zip"):
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
						# Test sleep mode
						elif split[2] == "!payload-low-power:3":
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
							# Delay
							time.sleep(0.5)
							# Sleep for 10 seconds
							rtc_driver.program_wakealarm_sleep("10")
						# Test standby mode
						elif split[2] == "!payload-low-power:1":
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
							# Delay
							time.sleep(0.5)
							# Sleep for 10 seconds
							rtc_driver.program_wakealarm_standby("10")
						# Activate sleep mode
						elif split[2] == "!payload-sleep:1":
							# Save
							if not os.path.exists("share/sleep.txt"):
								file_request = open("share/sleep.txt", "w")
								file_request.close()
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
						# Deactivate sleep mode
						elif split[2] == "!payload-sleep:0":
							# Save
							if os.path.exists("share/sleep.txt"):
								os.remove("share/sleep.txt")
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
						# Logger request
						elif split[2] == "!payload-logger:1":
							# Test request
							if not os.path.exists("temp/logger.txt"):
								file_request = open("temp/logger.txt", "w")
								file_request.close()
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
						# Cancel logger request
						elif split[2] == "!payload-logger:0":
							# Save
							if os.path.exists("temp/logger.txt"):
								os.remove("temp/logger.txt")
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
						# Detect SD card
						elif split[2] == "?payload-sd-detect":
							# Test SD car is present
							if system_driver.disk2_is_present():
								try:
									# Read capacity
									disk = psutil.disk_usage(system_driver.disk2_path())
									disk2_size = disk.total / (1024.0 ** 3)
									disk2_usage = float(disk.percent)
									reply = f"microSD: {disk2_size:.1f} GB ({disk2_usage:.1f}% used)"
									# Reply
									self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
								except (FileNotFoundError, PermissionError, OSError):
									# Error
									self._send_ascii("COMMANDACK,14,microSD: error")
							else:
								# Not installed
								self._send_ascii("COMMANDACK,22,microSD: not installed")
						# Format SD card
						elif split[2] == "!payload-sd-format":
							# Format SD in FAT32
							result = system_driver.disk2_format()
							# Reset parser state after long blocking operation
							rx_buffer.clear()
							last_frame_time = None
							# Reply
							if result:
								self._send_ascii("COMMANDACK,12,Command okay")
								# Delay
								time.sleep(0.5)
								# Restart
								system_driver.reboot()
							else:
								self._send_ascii("COMMANDACK,13,Command error")
						# Test SD card
						elif split[2] == "!payload-sd-test":
							# Write test file
							result = system_driver.disk2_test()
							# Reset parser state after long blocking operation
							rx_buffer.clear()
							last_frame_time = None
							# Reply
							if result:
								self._send_ascii("COMMANDACK,12,Command okay")
							else:
								self._send_ascii("COMMANDACK,13,Command error")
						# Clear all files from SD card
						elif split[2] == "!payload-sd-clear":
							# Clear everything in SD
							cleanup_folder(system_driver.disk2_path())
							# Reset parser state after long blocking operation
							rx_buffer.clear()
							last_frame_time = None
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
						# Fetch files from SD card
						elif split[2] == "!payload-sd-fetch":
							# Move files from SD
							move_from_sd()
							# Reset parser state after long blocking operation
							rx_buffer.clear()
							last_frame_time = None
							# Reply
							self._send_ascii("COMMANDACK,12,Command okay")
						# Execute Linux command
						elif split[2].startswith("!payload-execute:"):
							# Extract command
							command = split[2][17:].strip()
							try:
								# Execute
								reply = os.popen(command + " 2>&1").read().strip()
								if not reply:
									reply = "Command executed with no output"
							except Exception as e:
								reply = f"Error: {e}"
							# Reply
							self._send_ascii("COMMANDACK," + str(len(reply)) + "," + reply)
						# Error
						else:
							self._send_ascii("COMMANDACK,15,Unknown command")

					# LIST processing
					elif frame_string.startswith("LIST"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Logger request
						if os.path.exists("temp/logger.txt"):
							# Prepare logger extract
							logger_extract(96 * 1024)
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

					# FLIST processing
					elif frame_string.startswith("FLIST"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Logger request
						if os.path.exists("temp/logger.txt"):
							# Prepare logger extract
							logger_extract(192 * 1024)
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
							if (file_size > 0) and (file_size <= 1024 * 1024):
								# Reply
								self._send_ascii("FLISTACK,1," + list_name)
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
							self._send_ascii("FLISTACK,0")

					# GET processing
					elif frame_string.startswith("GET,"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Parse
						split = data_string.split(",")
						# Filename
						file_name = "payload/" + split[1]
						# Buffer size
						emap_buffer_size = int(split[2]) - len("DATA,xxx,xxxx,*CS")
						# Reply
						if os.path.exists(file_name):
							self._send_ascii("GETACK," + str(os.path.getsize(file_name)))
						else:
							self._send_ascii("GETNACK")

					# PUT processing
					elif frame_string.startswith("PUT,"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Parse
						split = data_string.split(",")
						# Configuration file
						if split[1] == "payload.cfg":
							# Filename
							file_name = "config/payload.cfg"
							# Remove file
							if os.path.exists(file_name):
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
							if os.path.exists(file_name):
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
					elif frame_string.startswith("DATA,"):
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
					elif frame_string.startswith("GETDATA"):
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
					elif frame_string.startswith("DATAACK,"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)
						# Parse
						split = data_string.split(",")
						# Last block
						if int(split[1]) > index_max:
							# Reply
							self._send_ascii("EOF")
							# Remove archive
							if os.path.exists(file_name):
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
					elif frame_string.startswith("DATANACK,"):
						# Print
						trace_log("EMAP     > Rx=$" + frame_string)

					# EOF processing
					elif frame_string.startswith("EOF"):
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

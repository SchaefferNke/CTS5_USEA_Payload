#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	emap.py
	"""

# Standard libraries
import sys
import zipfile

# Project libraries
from system.serial_lib import *
from system.timer_lib import *
from system.share_lib import *
from user.senso import TestSenso


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
class DriverEmap:
	"""
		DriverEmap class: manage communication with APMT navigation board
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.serial = DriverSerial("COM1", 57600, len("DATA,xxx,xxxx,*CS\r\n") + 512, 0.15)
		self.timer = DriverTimer(path, "emap")
		self.payload_step = DataShare("senso_step")
		self.payload = TestSenso()

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
		self.serial.write(frame_ascii.encode("ascii"))
		trace_log(trace_path, "EMAP     > Tx=" + frame_ascii)

	def send_binary(self, trace_path: str, frame: str, content: bytes):
		"""
			Send a frame on the serial port (without data detail on debug)

			Parameters:
				- trace_path (str): ...
				- frame (str): frame to send
				- content (bytes): frame content
			"""
		checksum = nmea_checksum_compute_binary(frame, content, len(frame), len(content))
		frame_ascii = "$" + frame + "[...]" + "*%0*X" % (2, checksum)
		time.sleep(0.05)
		string = "$" + frame
		self.serial.write(string.encode("ascii"))
		self.serial.write(content)
		string = "*%0*X" % (2, checksum)
		self.serial.write(string.encode("ascii"))
		trace_log(trace_path, "EMAP     > Tx=" + frame_ascii)

	# Get the time remaining before the task falls asleep
	def time_before_sleep(self) -> float:
		"""
			Get the time remaining before the task falls asleep

			Returns:
				- float: time remaining before the task falls asleep (sec)
			"""
		# Waiting for the next command
		return self.timer.remaining_time()

	# Run task
	def run(self):
		"""
			Working task
			"""
		# Scheduler
		manager(self)


# Create resources
path = "./"
emap_driver = DriverEmap()


# Logger extract
def logger_extract(size: int):
	"""
		Create extract of the logger file

		Parameters:
			- size (int): extract size (in bytes)
		"""
	# Create names
	log_src_name = path + "log/payload.log"
	log_dst_name = path + "temp/payload.log"
	zip_dst_name = path + "payload/payload.log.zip"
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


# Manager
def manager(self):
	global path
	file_name = ""
	index_cpt = 0
	index_max = 0
	emap_buffer_size = 128

	# Trace
	trace_log(path, "EMAP     > Activate")

	# Loop
	if self.serial.open():
		try:
			while True:

				# New character ?
				if self.serial.in_waiting() == 0:
					time.sleep(0.1)
					continue
				# Start timer
				self.timer.start_one_shot(0.999)
				# Wait start of frame
				if self.serial.read(1).decode() != "$":
					continue

				# Read frame
				frame_rx = self.serial.read(len("DATA,xxx,xxxx,*CS\r\n") + 512)
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
					trace_log(path, "EMAP     > [CHECKSUM]")
					# Continue
					continue
				# Extract data
				frame_data = frame_rx[0:-3]
				frame_string = frame_rx.decode("ascii", "ignore")
				data_string = frame_data.decode("ascii", "ignore")

				# VERSION processing
				if "VERSION" in frame_string[0:7]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Reply
					self.send_ascii(path, "VERSIONACK," + USEA_VERSION)

				# NAV processing
				elif "NAV," in frame_string[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# share information
					share = FileShare(path, "profile.txt")
					share.write(f"{int(split[1]):03}_{int(split[2]):02}")
					# Reply
					self.send_ascii(path, "NAVACK")

				# SEQ processing
				elif "SEQ," in frame_string[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# share information
					share = FileShare(path, "navigation.txt")
					share.write(split[1])
					# Reply
					self.send_ascii(path, "SEQACK")

				# CTRL processing
				elif "CTRL," in frame_string[0:5]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# share information
					if split[1] != "NONE":
						share = FileShare(path, "ctrl.txt")
						share.write(split[1])
					# share information
					share = FileShare(path, "pressure.txt")
					share.write(split[2])
					# Reply
					self.send_ascii(path, "CTRLACK")

				# CTD processing
				elif "CTD," in frame_string[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# share information
					share = FileShare(path, "ctd.txt")
					share.write(split[1] + "," + split[2] + "," + split[3])
					# share information
					share = FileShare(path, "pressure.txt")
					share.write(split[1])
					# Reply
					self.send_ascii(path, "CTDACK")

				# GPS processing
				elif "GPS," in frame_string[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
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
					# share information
					share = FileShare(path, "synchro.txt")
					share.write(f"{drift:.3f}")
					# Synchronize system clock
					# TODO: os.system("sudo date -u --set=%s" % utc.strftime("20%y-%m-%dT%H:%M:%S"))
					# Reply
					self.send_ascii(path, "GPSACK")

				# PING processing
				elif "PING" in frame_string[0:4]:
					# Sensor processing
					if self.payload_step.read() == USEA_PAYLOAD_STEP_TREAT:
						continue
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Reply
					self.send_ascii(path, "PINGACK")

				# COMMAND processing
				elif "COMMAND," in frame_string[0:8]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# User version
					if split[2] == "?payload-version":
						# Get version
						reply = self.payload.get_version()
						# Reply
						self.send_ascii(path, "COMMANDACK," + str(len(reply)) + "," + reply)
					# Application reset
					elif split[2] == "!payload-reset":
						# Reply
						self.send_ascii(path, "COMMANDACK")
						# Delay
						time.sleep(1.0)
						# Restart
						# TODO: os.system("sudo shutdown -r now")
						# TODO: os.system("sudo reboot -f")
					# Sensor test
					elif split[2] == "?payload-data":
						# Acquire data
						reply = self.payload.test()
						# Reply
						self.send_ascii(path, "COMMANDACK," + str(len(reply)) + "," + reply)
					# Logger request on
					elif split[2] == "!payload-logger:1":
						# Test request
						if not os.path.isfile(path + "share/logger.txt"):
							# Create request
							file_request = open(path + "share/logger.txt", "w")
							file_request.close()
					# Logger request off
					elif split[2] == "!payload-logger:0":
						# Test request
						if os.path.isfile(path + "share/logger.txt"):
							# Remove request
							os.remove(path + "share/logger.txt")
					# Error
					else:
						self.send_ascii(path, "COMMANDNACK")

				# LIST processing
				elif "LIST" in frame_string[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Logger request
					if os.path.isfile(path + "share/logger.txt"):
						# Prepare logger extract
						logger_extract(32 * 1024)
						# Remove request
						os.remove(path + "share/logger.txt")
					# Scan directories
					file_list = os.listdir(path + "payload/")
					# No file test
					no_file = True
					# Check file
					for list_name in file_list:
						# Get file size
						file_size = os.path.getsize(path + "payload/" + list_name)
						# File size is correct
						if (file_size > 0) and (file_size < 131072):
							# Reply
							self.send_ascii(path, "LISTACK,1," + list_name)
							# No file test
							no_file = False
							# Exit
							break
						# File size error
						else:
							# Keep file in memory
							continue
					# No file
					if no_file:
						# Reply
						self.send_ascii(path, "LISTACK,0")

				# GET processing
				elif "GET," in frame_string[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Filename
					file_name = path + "payload/" + split[1]
					# Buffer size
					emap_buffer_size = int(split[2]) - len("DATA,xxx,xxxx,*CS")
					# Reply
					if os.path.isfile(file_name):
						self.send_ascii(path, "GETACK," + str(os.path.getsize(file_name)))
					else:
						self.send_ascii(path, "GETNACK")

				# PUT processing
				elif "PUT," in frame_string[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Filename
					file_name = path + "config/" + split[1]
					# Remove file
					if os.path.isfile(file_name):
						os.remove(file_name)
					# Initialize data block
					index_cpt = 1
					# Reply
					self.send_ascii(path, "PUTACK,512")

				# DATA processing
				elif "DATA," in frame_string[0:5]:
					# Parse
					split = data_string.split(",")
					# Print
					if int(split[2]) > 0:
						trace_log(path, "EMAP     > Rx=$" + split[0] + "," + split[1] + "," + split[2] + ",[...]*" + frame_string[-2:])
					else:
						trace_log(path, "EMAP     > Rx=$" + split[0] + "," + split[1] + ",0*" + frame_string[-2:])
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

				# GETDATA processing
				elif "GETDATA" in frame_string[0:7]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
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
					self.send_binary(path, frame, content)

				# DATAACK processing
				elif "DATAACK," in frame_string[0:8]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)
					# Parse
					split = data_string.split(",")
					# Last block
					if int(split[1]) > index_max:
						# Reply
						self.send_ascii(path, "EOF")
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
							self.send_binary(path, frame, content)
						# Reply
						else:
							self.send_ascii(path, "DATA," + str(index_cpt) + ",0")

				# DATAACK processing
				elif "DATANACK," in frame_string[0:9]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)

				# EOF processing
				elif "EOF" in frame_string[0:3]:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string)

				# Unknown command
				else:
					# Print
					trace_log(path, "EMAP     > Rx=$" + frame_string + " [UNDEFINED]")

		# Error
		except Exception as err:
			# Trace
			print(err)
			print(traceback.format_exc())
			# Trace
			trace_log(path, "EMAP     > [ERROR]")

	# Close serial port
	self.serial.close()


# Test function
if __name__ == "__main__":
	"""
		Module test function
		"""
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")
	path = "../"
	# Allocate resource
	emap = DriverEmap()
	# Run
	emap.run()

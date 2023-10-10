#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	emap.py
	"""

# Standard libraries
import sys
import os

# Project libraries
from system.const import *
from system.serial_lib import *
from system.timer_lib import *
from system.share_lib import *
from user.sensor import TestSensor

# Global var
global path, frame_emap, frame_print


# Compute NMEA checksum (receive)
def nmea_checksum_check(frame: str) -> bool:
	"""
		Check the checksum value of a received frame

		Parameters:
			- frame (str): bytes read from the serial port

		Returns:
			- bool: True if the frame is correct
		"""
	if frame[0] != "$":
		return False
	if frame[-3] != "*":
		return False
	checksum = 0
	for c in frame[1:-3]:
		checksum ^= ord(c)
	if int(frame[-2:], 16) == checksum:
		return True
	return False


# Compute NMEA checksum (transmit)
def nmea_checksum_compute(frame: str, count: int) -> int:
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
class DriverEmap:
	"""
		DriverEmap class: manage communication with APMT navigation board
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.serial = DriverSerial("COM1", 57600, len("DATA,xxx,xxxx,*CS\r\n") + 512, 0.15)
		self.timer = DriverTimer(path, "emap")
		self.sensor_step = DataShare("sensor_step")
		self.sensor = TestSensor()

	# Send frame over EMAP link
	def reply(self, trace_path: str, frame: str):
		"""
			Send a frame on the serial port

			Parameters:
				- trace_path (str): ...
				- frame (str): frame to send
			"""
		global frame_emap, frame_print

		frame_print = "$" + frame + "*%0*X" % (2, nmea_checksum_compute(frame, len(frame)))
		frame_emap = "$" + frame + "*%0*X" % (2, nmea_checksum_compute(frame, len(frame)))
		time.sleep(0.05)
		self.serial.write(frame_emap.encode())
		trace_log(trace_path, "EMAP     > Tx=" + frame_print)

	def reply_data_packet(self, trace_path: str, frame: str, content: str):
		"""
			Send a frame on the serial port (without data detail on debug)

			Parameters:
				- trace_path (str): ...
				- frame (str): frame to send
				- content (str): frame content
			"""
		global frame_emap, frame_print

		frame_print = "$" + frame + "[...]" + "*%0*X" % (2, nmea_checksum_compute(frame + content, len(frame) + len(content)))
		frame_emap = "$" + frame + content + "*%0*X" % (2, nmea_checksum_compute(frame + content, len(frame) + len(content)))
		time.sleep(0.05)
		self.serial.write(frame_emap.encode())
		trace_log(trace_path, "EMAP     > Tx=" + frame_print)

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


# Manager
def manager(self):
	global path
	file_name = ""
	index_cpt = 0
	index_max = 0

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
				frame_rx = "$" + self.serial.read(len("DATA,xxx,xxxx,*CS\r\n") + 512).decode()
				# End of line sequence (optional)
				if frame_rx[-2] == "\r" and frame_rx[-1] == "\n":
					frame_rx = frame_rx[0:-2]
				elif frame_rx[-1] == "\n":
					frame_rx = frame_rx[0:-1]
				elif frame_rx[-1] == "\r":
					frame_rx = frame_rx[0:-1]
				# Verify checksum
				if not nmea_checksum_check(frame_rx):
					# Print
					trace_log(path, "EMAP     > [CHECKSUM]")
					# Continue
					continue
				# Extract data
				frame_data = frame_rx[1:-3]
				# Parse
				split = frame_data.split(",")

				# VERSION processing
				if "VERSION" in frame_data[0:7]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Reply
					self.reply(path, "VERSIONACK," + USEA_VERSION)

				# NAV processing
				elif "NAV," in frame_data[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Timestamp
					now = datetime.datetime.now()
					# share information
					share = FileShare(path, "profile.txt")
					share.write(f"{int(split[1]):03}_{int(split[2]):02}")
					# Reply
					self.reply(path, "NAVACK")

				# SEQ processing
				elif "SEQ," in frame_data[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Timestamp
					now = datetime.datetime.now()
					# share information
					share = FileShare(path, "navigation.txt")
					share.write(split[1])
					# Reply
					self.reply(path, "SEQACK")

				# CTRL processing
				elif "CTRL," in frame_data[0:5]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Timestamp
					now = datetime.datetime.now()
					# share information
					if split[1] != "NONE":
						share = FileShare(path, "ctrl.txt")
						share.write(split[1])
					# share information
					share = FileShare(path, "pressure.txt")
					share.write(split[2])
					# Reply
					self.reply(path, "CTRLACK")

				# CTD processing
				elif "CTD," in frame_data[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Timestamp
					now = datetime.datetime.now()
					# share information
					share = FileShare(path, "ctd.txt")
					share.write(split[1] + "," + split[2] + "," + split[3])
					# share information
					share = FileShare(path, "pressure.txt")
					share.write(split[1])
					# Reply
					self.reply(path, "CTDACK")

				# GPS processing
				elif "GPS," in frame_data[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Timestamp
					now = datetime.datetime.now()
					utc = now.replace(year=2000 + int(split[1][2:4]), month=int(split[1][4:6]), day=int(split[1][6:8]), hour=int(split[2][0:2]), minute=int(split[2][2:4]), second=int(split[2][4:6]),microsecond=0)
					# Drift
					drift = (now - utc).total_seconds()
					# share information
					share = FileShare(path, "synchro.txt")
					share.write(f"{drift:.3f}")
					# Reply
					self.reply(path, "GPSACK")

				# PING processing
				elif "PING" in frame_data[0:4]:
					# Sensor processing
					if self.sensor_step.read() == USEA_SENSOR_STEP_TREAT:
						continue
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Reply
					self.reply(path, "PINGACK")

				# COMMAND processing
				elif "COMMAND," in frame_data[0:8]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Sensor command
					if split[2] == "?payload-data":
						# Acquire data
						if self.sensor.test():
							self.reply(path, "COMMANDACK,2,ok")
						else:
							self.reply(path, "COMMANDACK,5,error")
					# Error
					else:
						self.reply(path, "COMMANDNACK")

				# LIST processing
				elif "LIST" in frame_data[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Scan directories
					file_list = os.listdir(path + "payload/")
					# No file test
					no_file = True
					# Check file
					for file_name in file_list:
						# Get file size
						file_size = os.path.getsize(path + "payload/" + file_name)
						# File size is correct
						if (file_size > 0) and (file_size < 131072):
							# Reply
							self.reply(path, "LISTACK," + file_name)
							# No file test
							no_file = False
							# Exit
							break
						# File size error
						else:
							continue
					# Error
					if no_file:
						self.reply(path, "LISTACK,0")

				# GET processing
				elif "GET," in frame_data[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Filename
					file_name = path + "payload/" + split[1]
					# Reply
					if os.path.isfile(file_name):
						self.reply(path, "GETACK," + str(os.path.getsize(file_name)))
					else:
						self.reply(path, "GETNACK")

				# PUT processing
				elif "PUT," in frame_data[0:4]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Filename
					file_name = path + "config/" + split[1]
					# Remove file
					if os.path.isfile(file_name):
						os.remove(file_name)
					# Initialize data block
					index_cpt = 1
					# Reply
					self.reply(path, "PUTACK")

				# DATA processing
				elif "DATA," in frame_data[0:5]:
					# Print
					if int(split[2]) > 0:
						trace_log(path,"EMAP     > Rx=$" + split[0] + "," + split[1] + "," + split[2] + ",[...]*" + frame_rx[-2:])
					else:
						trace_log(path, "EMAP     > Rx=$" + split[0] + "," + split[1] + ",0*" + frame_rx[-2:])
					# Check size
					if split[2] == "0":
						# Reply
						self.reply(path, "DATAACK," + split[1])
					# Check index
					elif index_cpt == int(split[1]):
						# Next block
						index_cpt += 1
						# Write into file
						file_handle = open(file_name, "a+")
						content = file_handle.write(frame_data[len("DATA,,,") + len(split[1]) + len(split[2]):])
						file_handle.close()
						# Reply
						self.reply(path, "DATAACK," + split[1])
					# Error
					else:
						self.reply(path, "DATANACK")

				# GETDATA processing
				elif "GETDATA," in frame_data[0:8]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Initialize data blocks
					index_cpt = 1
					index_max = round(os.path.getsize(file_name) / 512) + 1
					# Read from file
					file_handle = open(file_name, "r")
					content = file_handle.read(512)
					file_handle.close()
					# Format
					frame = "DATA,1," + str(len(content)) + ","
					# Reply
					self.reply_data_packet(path, frame, content)

				# DATAACK processing
				elif "DATAACK," in frame_data[0:8]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)
					# Check block
					if int(split[1]) > index_max:
						self.reply(path, "EOF")
					elif int(split[1]) == index_cpt:
						# Read from file
						file_handle = open(file_name, "r")
						file_handle.seek(index_cpt * 512)
						content = file_handle.read(512)
						file_handle.close()
						# Next block
						index_cpt += 1
						# Reply
						if len(content) > 0:
							# Format
							frame = "DATA," + str(index_cpt) + "," + str(len(content)) + ","
							# Reply
							self.reply_data_packet(path, frame, content)
						# Reply
						else:
							self.reply(path, "DATA," + str(index_cpt) + ",0")

				# EOF processing
				elif "EOF," in frame_data[0:8]:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx)

				# Unknown command
				else:
					# Print
					trace_log(path, "EMAP     > Rx=" + frame_rx + " [UNDEFINED]")

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

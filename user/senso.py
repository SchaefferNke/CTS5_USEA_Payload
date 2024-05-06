#!/bin/python
# -*- coding: utf-8 -*-
"""
	senso.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-05-06"
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
from system.io_lib import DriverIOOutput, DriverIOInput
from system.serial_lib import DriverSerial
from system.timer_lib import DriverTimer
from system.share_lib import FileShare, DataShare, get_navigation, get_profile
from system.technical import DriverTechnicalUser
from system.trace_lib import trace_log
from system.const import *

# Versioning
SENSO_VERSION = "1.0.0"


# Acquisition process
def acquisition_process(self, string: str) -> bool:
	"""
		Sample acquisition process

		Returns:
			- bool: True if the acquisition process is successful
	"""
	# Print
	trace_log("SENSO    > " + string)
	# Power-on
	self._io_power.set_on()
	# Warm-up
	time.sleep(1.5)
	# Acquisition
	frame_data = self._serial.receive_ascii(3.0)
	# Treatment
	if "SENSO,D," in frame_data[0:8]:
		# Parse
		split = frame_data.split(",")
		# Print
		trace_log("SENSO    > Rx=" + frame_data)
		# Extract
		self.output.timestamp = datetime.datetime.now().timestamp()
		self.output.channel1 = float(split[2])
		self.output.channel2 = float(split[3])
		self.output.channel3 = float(split[4])
		# Count success
		if string == "Acquire":
			self._tech.diagnosis_count_success()
		# Result
		result = True
	# Error
	else:
		# Print
		trace_log("SENSO    > Time-out")
		# Count error
		if string == "Acquire":
			self._tech.diagnosis_count_error()
		# Result
		result = False
	# Count alarm
	if string == "Acquire":
		if not self._io_alarm.is_on():
			self._tech.diagnosis_count_alarm()
	# Power-off
	self._io_power.set_off()
	# Delay before new power-on (for proper operation of the sensor)
	time.sleep(0.5)
	# Result
	return result


# Class definition
class DataSenso:
	"""
		DataSenso class: sensor data

		Attributes:
			- timestamp (float): timestamp
			- channel1 (float): channel 1 raw value
			- channel2 (float): channel 2 raw value
			- channel3 (float): channel 3 raw value
	"""

	# Output
	def __init__(self):
		self.timestamp = 0.0
		self.channel1 = 0.0
		self.channel2 = 0.0
		self.channel3 = 0.0


# Class definition
class DriverSenso:
	"""
		DriverSenso class: manage acquisition of sensor
	"""

	# Create resource
	def __init__(self):
		# Manager
		self._active = False
		self._step = USEA_PAYLOAD_STEP_IDLE
		self._io_power = DriverIOOutput("GPIO_3_20")
		self._io_alarm = DriverIOInput("GPIO_5_5")
		self._serial = DriverSerial("COM_5", 19200, 128, 0.15)
		self._timer = DriverTimer("senso")
		self._share_step = DataShare("payload_step")
		self._tech = DriverTechnicalUser("SENSO")
		# Output
		self.output = DataSenso()
		self.output.timestamp = 0.0
		self.output.channel1 = 0.0
		self.output.channel2 = 0.0
		self.output.channel3 = 0.0

	# Get time before next activity
	def get_time_before_activity(self) -> float:
		"""
			Get the time remaining before the next activity

			Returns:
				- float: time remaining before the next activity (sec)
		"""
		# Waiting for the next measurement
		if not self._active:
			result = 3600.0
		elif self._step == USEA_PAYLOAD_STEP_IDLE:
			result = 3600.0
		elif self._step == USEA_PAYLOAD_STEP_RECORD:
			result = self._timer.remaining_time()
		else:
			result = 0.0
		# Result
		return result

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Scheduler
		manager(self)

	# Acquire data
	def acquire_sample(self) -> bool:
		"""
			Sample acquisition process

			Returns:
				- bool: True if the acquisition process is successful
		"""
		# Acquire
		return acquisition_process(self, "Acquire")

	# Share information string
	def share_info(self):
		"""
			Share information string
		"""
		# Share information
		share = FileShare("user.txt")
		# Processing step
		if self._step == USEA_PAYLOAD_STEP_IDLE:
			share.write("IDLE")
		elif self._step == USEA_PAYLOAD_STEP_RECORD:
			share.write("RECORD")
		elif self._step == USEA_PAYLOAD_STEP_RECORDING:
			share.write("RECORDING")
		elif self._step == USEA_PAYLOAD_STEP_SURFACE:
			share.write("SURFACE")
		elif self._step == USEA_PAYLOAD_STEP_TREAT:
			share.write("TREAT")
		else:
			share.write("?")


# Class definition
class TestSenso:
	"""
		TestSenso class: manage test commands with sensor
	"""

	# Create resource
	def __init__(self):
		# Manager
		self._io_power = DriverIOOutput("GPIO_3_20")
		self._io_alarm = DriverIOInput("GPIO_5_5")
		self._serial = DriverSerial("COM_5", 19200, 128, 0.15)
		# Output
		self.output = DataSenso()
		self.output.timestamp = 0.0
		self.output.channel1 = 0.0
		self.output.channel2 = 0.0
		self.output.channel3 = 0.0

	# Get version
	@staticmethod
	def get_version(self) -> str: return SENSO_VERSION

	# Dummy measurement
	def get_data(self) -> str:
		"""
			Dummy measurement

			Returns:
				- str: result string (eg: "c1=15.367", "no reply" if error)
		"""
		# Acquire
		if acquisition_process(self, "Test"):
			# Reply
			return "c1=" + f"{self.output.channel1:.3f}" +\
				", c2=" + f"{self.output.channel2:.3f}" +\
				", c3=" + f"{self.output.channel3:.3f}"
		# Error
		else:
			# Reply
			return "no reply"

	# Test sensor
	def test(self) -> str:
		"""
			Test process

			Returns:
				- str: result string (eg: "senso   : ok", xxxxxxxx: ok/error format)
		"""
		# Acquire
		if acquisition_process(self, "Autotest"):
			# Reply
			return "senso   : ok"
		# Error
		else:
			# Reply
			return "senso   : error"


# Compression
def compress():
	"""
		Compress the data files
	"""
	# Create names
	zip_src_name = "payload/" + get_profile() + "_payload.csv"
	zip_tmp_name = "temp/" + get_profile() + "_payload.hex"
	zip_dst_name = "payload/" + get_profile() + "_payload.hex"
	# No file to compress
	if not os.path.isfile(zip_src_name):
		return
	# Remove src archive
	if os.path.isfile(zip_tmp_name):
		os.remove(zip_tmp_name)
	# Remove dst archive
	if os.path.isfile(zip_dst_name):
		os.remove(zip_dst_name)
	# Create archive
	zip_file = zipfile.ZipFile(zip_tmp_name, "w")
	# Add file
	zip_file.write(zip_src_name, get_profile() + "_payload.csv", compress_type=zipfile.ZIP_DEFLATED)
	# Remove file
	os.remove(zip_src_name)
	# Close archive
	zip_file.close()
	# Move archive
	os.rename(zip_tmp_name, zip_dst_name)


# Create resources
senso_driver = DriverSenso()


# Manager
def manager(self):
	"""
		Running task
	"""

	file_name = ""

	# Trace
	trace_log("SENSO    > Activate")

	# Activate task
	self._active = True
	# Synchronize timer
	self._timer.wait_until_synchro()
	# Start timer
	self._timer.start_base_time(15.0)
	# Share step
	self._share_step.write(self._step)
	# Share info
	self.share_info()

	# Loop
	try:
		while True:

			# Sensor activated ?
			if not self._active:
				time.sleep(0.1)
				continue

			# Read resource
			navigation = get_navigation()

			# Wait
			if self._step == USEA_PAYLOAD_STEP_IDLE:
				# Ascent step
				if (
					(navigation == USEA_NAVIGATION_STATE_ASCENT) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_1) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_2) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_3)):
					# Create file name
					file_name = "payload/" + get_profile() + "_payload.csv"
					# Print
					trace_log("SENSO    > Start acquisition")
					# Start recording
					self._step = USEA_PAYLOAD_STEP_RECORD
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()
					# Reset error flags counters
					self._tech.diagnosis_reset()
				# Wait
				else:
					time.sleep(0.1)

			# Record
			elif self._step == USEA_PAYLOAD_STEP_RECORD:
				# Ascent step
				if (
					(navigation == USEA_NAVIGATION_STATE_ASCENT) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_1) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_2) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_3)):
					# Sensor broken
					if not self._tech.diagnosis_is_broken():
						# Acquisition rate
						if self._timer.is_tick():
							# Recording in progress
							self._step = USEA_PAYLOAD_STEP_RECORDING
							# Share info
							self.share_info()
							# Acquire
							if self.acquire_sample():
								# Print
								trace_log("SENSO    > Record")
								# Store data
								file = open(file_name, "a+")
								file.write(
									f"{self.output.timestamp:.3f}" + "," +
									f"{self.output.channel1:.3f}" + "," +
									f"{self.output.channel2:.3f}" + "," +
									f"{self.output.channel3:.3f}" + "\n")
								file.close()
							# Failure
							else:
								# Too many successive errors
								if self._tech.diagnosis_get_successive_failure() >= 3:
									# Declare the sensor broken
									self._tech.diagnosis_count_broken()
									# Print
									trace_log("SENSO    > Broken")
							# Recording finished
							self._step = USEA_PAYLOAD_STEP_RECORD
							# Share info
							self.share_info()
						# Wait
						else:
							time.sleep(0.1)
					# Wait
					else:
						time.sleep(0.1)
				# Surface step
				elif (
					(navigation == USEA_NAVIGATION_STATE_SUB_SURFACE) or
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_INCREASE) or
					(navigation == USEA_NAVIGATION_STATE_SURFACE_ACQUISITION)):
					# Print
					trace_log("SENSO    > Stop acquisition")
					# Stop recording
					self._step = USEA_PAYLOAD_STEP_SURFACE
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()
				# Other
				else:
					# Print
					trace_log("SENSO    > Stop acquisition")
					# Stop recording
					self._step = USEA_PAYLOAD_STEP_IDLE
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()

			# Surface
			elif self._step == USEA_PAYLOAD_STEP_SURFACE:
				# Treatment step
				if navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Print
					trace_log("SENSO    > Start processing")
					# Start processing
					self._step = USEA_PAYLOAD_STEP_TREAT
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()
					# Simulate treatment delay
					# TODO: for test
					time.sleep(5.0)
					# Save errors
					self._tech.diagnosis_save()
					# Compress files
					compress()
					# Simulate treatment delay
					# TODO: for test
					time.sleep(5.0)
					# Print
					trace_log("SENSO    > Stop processing")
					# Stop processing
					self._step = USEA_PAYLOAD_STEP_IDLE
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()
				# Surface step
				elif (
					(navigation == USEA_NAVIGATION_STATE_SUB_SURFACE) or
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_INCREASE) or
					(navigation == USEA_NAVIGATION_STATE_SURFACE_ACQUISITION)):
					# Ignore
					time.sleep(0.1)
				# Other
				else:
					# Stop recording
					self._step = USEA_PAYLOAD_STEP_IDLE
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()

			# Other
			else:
				time.sleep(0.1)

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log("SENSO    > [ERROR]")


# Test function
if __name__ == "__main__":
	# Run
	senso_driver.run()

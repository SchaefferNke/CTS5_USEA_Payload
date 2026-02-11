#!/bin/python
# -*- coding: utf-8 -*-
"""
	senso.py
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
from system.share_lib import FileShare, DataShare, get_navigation, get_profile, get_pressure
from system.technical import DriverTechnicalUser
from system.trace_lib import trace_log
from system.const import *

# Versioning
SENSO_VERSION = "1.0.1"

# Senso output format
SENSO_OUTPUT_PHY_3 = False
SENSO_OUTPUT_RAW_50 = True


# Validate raw value
def clamp_raw(val: int) -> int:
	if val < 0:
		return 0
	if val > 262143:
		return 262143
	return val


# Analyse frame
def _parse_senso_frame(self, frame_data: str) -> bool:
	"""
		Parse SENSO frame and fill output structure

		Returns:
			- bool: True if parsing is successful
	"""
	# Check header
	if not frame_data or not frame_data.startswith("SENSO,D,"):
		trace_log("SENSO    > Frame parse error (no header)")
		return False
	# Try
	try:
		# Parse
		split = frame_data.split(",")
		# Reference
		self.output.timestamp = datetime.datetime.now().timestamp()
		self.output.pressure = get_pressure()
		# Extract
		if SENSO_OUTPUT_PHY_3:
			if len(split) < 5:
				trace_log(f"SENSO    > Frame parse error (bad size: {len(split)})")
				return False
			self.output.channel1 = float(split[2])
			self.output.channel2 = float(split[3])
			self.output.channel3 = float(split[4])
		elif SENSO_OUTPUT_RAW_50:
			if len(split) < 61:
				trace_log(f"SENSO    > Frame parse error (bad size: {len(split)})")
				return False
			self.output.channel_a1 = float(split[5])
			self.output.channel_a2 = float(split[6])
			self.output.channel_a3 = float(split[7])
			for i in range(16):
				value = int(split[i + 8])
				raw = value - 4900
				self.output.channels_a[i] = clamp_raw(raw)
			self.output.channel_b1 = float(split[24])
			self.output.channel_b2 = float(split[25])
			self.output.channel_b3 = float(split[26])
			for i in range(34):
				value = int(split[i + 27])
				raw = value - 4900
				self.output.channels_b[i] = clamp_raw(raw)
	# Error
	except (IndexError, ValueError) as e:
		# Print
		trace_log(f"SENSO    > Frame parse error ({e})")
		# Result
		return False
	# Result
	return True


# Acquisition process (with power management)
def acquisition_process_with_power(self, string: str) -> bool:
	"""
		Sample acquisition process (with power management)

		Returns:
			- bool: True if the acquisition process is successful
	"""
	# Power-on
	self._io_power.set_on()
	# Warm-up
	time.sleep(2.5)
	# Acquisition
	frame_data = self._serial.receive_ascii(1.5)
	print(frame_data)
	# Treatment
	if _parse_senso_frame(self, frame_data):
		# Print
		trace_log("SENSO    > " + f"{self.output.timestamp:.1f}" + ',' + f"{self.output.pressure:.2f}" + ',' + frame_data[8:])
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
		if not self._io_alarm.get():
			self._tech.diagnosis_count_alarm()
	# Power-off
	self._io_power.set_off()
	# Delay before new power-on (for proper operation of the sensor)
	time.sleep(0.5)
	# Result
	return result


# Acquisition process (without power management)
def acquisition_process_no_power(self, string: str) -> bool:
	"""
		Sample acquisition process (without power management)

		Returns:
			- bool: True if the acquisition process is successful
	"""
	# Acquisition
	frame_data = self._serial.receive_ascii(1.5)
	# Treatment
	if _parse_senso_frame(self, frame_data):
		# Print
		trace_log("SENSO    > " + f"{self.output.timestamp:.1f}" + ',' + f"{self.output.pressure:.2f}" + ',' + frame_data[8:])
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
		if not self._io_alarm.get():
			self._tech.diagnosis_count_alarm()
	# Result
	return result


# Class definition
class DataSenso:
	"""
		DataSenso class: sensor data

		Attributes:
			[SENSO_OUTPUT_PHY_3]
			- timestamp (float): timestamp
			- pressure (float): pressure value
			- channel1 (float): channel 1 physical value
			- channel2 (float): channel 2 physical value
			- channel3 (float): channel 3 physical value
			[SENSO_OUTPUT_RAW_50]
			- timestamp (float): timestamp
			- pressure (float): pressure value
			- channel_a1 (float): channel a physical value 1
			- channel_a2 (float): channel a physical value 2
			- channel_a3 (float): channel a physical value 3
			- channels_a[0] (unsigned int): channel a1 raw value
			- ...
			- channels_a[15] (unsigned int): channel a16 raw value
			- channel_b1 (float): channel b physical value 1
			- channel_b2 (float): channel b physical value 2
			- channel_b3 (float): channel b physical value 3
			- channels_b[0] (unsigned int): channel b1 raw value
			- ...
			- channels_b[15] (unsigned int): channel b34 raw value
	"""

	# Output
	if SENSO_OUTPUT_PHY_3:
		def __init__(self):
			self.timestamp = 0.0
			self.pressure = 0.0
			self.channel1 = 0.0
			self.channel2 = 0.0
			self.channel3 = 0.0
	elif SENSO_OUTPUT_RAW_50:
		def __init__(self):
			self.timestamp = 0.0
			self.pressure = 0.0
			self.channel_a1 = 0.0
			self.channel_a2 = 0.0
			self.channel_a3 = 0.0
			self.channels_a = [0] * 16
			self.channel_b1 = 0.0
			self.channel_b2 = 0.0
			self.channel_b3 = 0.0
			self.channels_b = [0] * 34


# Class definition
class DriverSenso:
	"""
		DriverSenso class: manage acquisition of sensor
	"""

	# Create resource
	def __init__(self, user_index: int):
		# Manager
		self._user_index = user_index
		self._active = False
		self._step = USEA_USER_STEP_IDLE
		self._io_power = DriverIOOutput("GPIO_3_20")
		self._io_alarm = DriverIOInput("GPIO_5_5")
		self._serial = DriverSerial("COM_5", 19200, 0.5)
		self._timer = DriverTimer("senso")
		if user_index == 0:
			self._share_step = DataShare("user_step")
		else:
			self._share_step = DataShare(f"user{user_index}_step")
		self._tech = DriverTechnicalUser("SENSO")
		# Output
		self.output = DataSenso()

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
		elif self._step == USEA_USER_STEP_IDLE:
			result = 3600.0
		elif self._step == USEA_USER_STEP_RECORD:
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
		return acquisition_process_no_power(self, "Acquire")

	# Share information string
	def share_info(self):
		"""
			Share information string
		"""
		# Share information
		if self._user_index == 0:
			file_name = "user.txt"
		else:
			file_name = f"user{self._user_index}.txt"
		user_info = FileShare(file_name)
		# Processing step
		step_name = next((name for name, value in USEA_USER_STATE_MAP.items() if value == self._step), "?")
		user_info.write(step_name)


# Class definition
class TestSenso:
	"""
		TestSenso class: manage test commands with sensor
	"""

	# Create resource
	def __init__(self, user_index: int):
		# Manager
		self._user_index = user_index
		self._io_power = DriverIOOutput("GPIO_3_20")
		self._io_alarm = DriverIOInput("GPIO_5_5")
		self._serial = DriverSerial("COM_5", 19200, 0.5)
		# Output
		self.output = DataSenso()

	# Get version
	# noinspection PyMethodMayBeStatic
	def get_version(self) -> str: return SENSO_VERSION

	# Dummy measurement
	def get_data(self) -> str:
		"""
			Dummy measurement

			Returns:
				- str: result string (eg: "c1=15.367", "no reply" if error)
		"""
		# Acquire
		if acquisition_process_with_power(self, "Test"):
			# Reply
			if SENSO_OUTPUT_PHY_3:
				return "c1=" + f"{self.output.channel1:.3f}" +\
					", c2=" + f"{self.output.channel2:.3f}" +\
					", c3=" + f"{self.output.channel3:.3f}"
			elif SENSO_OUTPUT_RAW_50:
				return "a3=" + str(self.output.channel_a3) +\
					",... , b3=" + str(self.output.channel_b3)
		# Error
		else:
			# Reply
			return "no reply"

	# Test sensor
	def test(self) -> str:
		"""
			Test process

			Returns:
				- str: result string (eg: "senso   : ok", senso   : ok/error format)
		"""
		# Acquire
		if acquisition_process_with_power(self, "Autotest"):
			# Reply
			return "senso   : ok"
		# Error
		else:
			# Reply
			return "senso   : error"


# Create resources
senso_driver = DriverSenso(0)


# Manager
def manager(self):
	"""
		Running task
	"""

	file_name = ""
	timestamp_record = 0.0
	start_date = ""

	# Trace
	trace_log("SENSO    > Activate")

	# Activate task
	self._active = True
	# Synchronize timer
	self._timer.wait_until_synchro()
	# Start timer
	self._timer.start_base_time(1.0)
	# Share step
	self._share_step.write(self._step)
	# Share info
	self.share_info()

	# Loop
	while True:
		try:

			# Sensor activated ?
			if not self._active:
				time.sleep(0.1)
				continue

			# Read resources
			navigation = get_navigation()
			pressure = get_pressure()

			# Wait
			if self._step == USEA_USER_STEP_IDLE:
				# Ascent step
				if navigation == USEA_NAVIGATION_STATE_ASCENT:
					# Create file name
					file_name = "payload/" + get_profile() + "_senso.csv"
					# Get start date
					now = datetime.datetime.now()
					start_date = now.strftime("%d/%m/%y %H:%M:%S\n")
					# Print
					trace_log("SENSO    > Start acquisition")
					# Start recording
					self._step = USEA_USER_STEP_RECORD
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()
					# Reset error flags counters
					self._tech.diagnosis_reset()
					# Power-on
					self._io_power.set_on()
					# Warm-up
					time.sleep(2.5)
				# Wait
				else:
					time.sleep(0.1)

			# Record
			elif self._step == USEA_USER_STEP_RECORD:
				# Ascent step
				if (
					(navigation == USEA_NAVIGATION_STATE_ASCENT) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_1) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_2) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_3) or
					(navigation == USEA_NAVIGATION_STATE_SUB_SURFACE)):
					# Recording period
					if   pressure > 1000.0: record_period = 30.0  # noqa: E203,E222,E271,E701
					elif pressure >  300.0: record_period = 10.0  # noqa: E203,E222,E271,E701
					elif pressure >  100.0: record_period =  2.0  # noqa: E203,E222,E271,E701
					elif pressure >    2.0: record_period =  1.0  # noqa: E203,E222,E271,E701
					else                  : record_period = 20.0  # noqa: E203,E222,E271,E701
					# Base time count
					if self._timer.is_tick():
						# Acquisition in progress
						self._step = USEA_USER_STEP_SAMPLE
						# Share info
						self.share_info()
						# Acquire
						if self.acquire_sample():
							# Recording period management
							if self.output.timestamp >= timestamp_record + record_period:
								# Update record timestamp
								timestamp_record = self.output.timestamp
								# Store data
								with open(file_name, "a+") as file:
									if SENSO_OUTPUT_PHY_3:
										file.write(
											f"{self.output.timestamp:.1f}" + ";" +
											f"{self.output.pressure:.2f}" + ";" +
											f"{self.output.channel1:.3f}" + ";" +
											f"{self.output.channel2:.3f}" + ";" +
											f"{self.output.channel3:.3f}" + "\n")
									elif SENSO_OUTPUT_RAW_50:
										file.write(f"{self.output.pressure:.2f}" + ";")
										for i in range(16):
											file.write(str(self.output.channels_a[i]) + ";")
										file.write(
											f"{self.output.channel_b1:.1f}" + ";" +
											f"{self.output.channel_b2:.1f}" + ";" +
											f"{self.output.channel_b3:.1f}" + "\n")
						# Acquisition finished
						self._step = USEA_USER_STEP_RECORD
						# Share info
						self.share_info()
					# Wait
					else:
						time.sleep(0.1)
				# Other
				else:
					# Get stopping date
					now = datetime.datetime.now()
					stop_date = now.strftime("%d/%m/%y %H:%M:%S\n")
					# Save start and stop dates
					with open(file_name, "a+") as file:
						file.write(start_date + stop_date)
					# Print
					trace_log("SENSO    > Stop acquisition")
					# Stop recording
					self._step = USEA_USER_STEP_SURFACE
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()
					# Power-off
					self._io_power.set_off()

			# Surface
			elif self._step == USEA_USER_STEP_SURFACE:
				# Wait for processing
				if (
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_INCREASE) or
					(navigation == USEA_NAVIGATION_STATE_SURFACE_ACQUISITION)):
					time.sleep(0.1)
				# Treatment step
				elif (
					(navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING) or
					(navigation == USEA_NAVIGATION_STATE_GPS)):
					# Print
					trace_log("SENSO    > Processing")
					# Start processing
					self._step = USEA_USER_STEP_TREAT
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()
					# Save errors
					self._tech.diagnosis_save()
					# Stop processing
					self._step = USEA_USER_STEP_IDLE
					# Share step
					self._share_step.write(self._step)
					# Share info
					self.share_info()
				# Other
				else:
					# Stop recording
					self._step = USEA_USER_STEP_IDLE
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

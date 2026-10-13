#!/bin/python
# -*- coding: utf-8 -*-
"""
	senso.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-10-12"
__version__ = "1.0.3"

# Standard libraries
import os
import sys
import time
import datetime
import traceback
from enum import Enum

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
SENSO_VERSION = __version__


class AcquisitionMode(Enum):
	PROFILE = 1
	DATA = 2
	AUTOTEST = 3


# Class definition
class DataSenso:
	"""
		DataSenso class: sensor data

		Attributes:
			- timestamp (float): timestamp
			- pressure (float): pressure value
			- channel1 (float): channel 1 physical value
			- channel2 (float): channel 2 physical value
			- channel3 (float): channel 3 physical value
	"""

	# Output
	def __init__(self):
		self.timestamp = 0.0
		self.pressure = 0.0
		self.channel1 = 0.0
		self.channel2 = 0.0
		self.channel3 = 0.0


# Class definition
class DriverSenso:
	"""
		DriverSenso class: manage acquisition of sensor
	"""

	# Create resource
	def __init__(self, user_index: int):
		# Manager
		self._stop = False
		self._user_index = user_index
		self._active = False
		self._step = USEA_USER_STEP_IDLE
		self._io_power = DriverIOOutput("GPIO_3_19")
		self._io_alarm = DriverIOInput("GPIO_1_0")
		self._serial = DriverSerial("COM_4", 19200, 0.5)
		self._timer = DriverTimer("senso")
		if user_index == 0:
			self._share_step = DataShare("user_step")
			self._share_info = FileShare("user.txt")
		else:
			self._share_step = DataShare(f"user{user_index}_step")
			self._share_info = FileShare(f"user{self._user_index}.txt")
		self._tech = DriverTechnicalUser("SENSO")
		# Output
		self.output = DataSenso()

	# Analyse frame
	def _parse_senso_frame(self, frame_data: str) -> bool:
		"""
			Parse SENSO frame and fill output structure

			Returns:
				- bool: True if parsing is successful
		"""
		# No data
		if not frame_data or frame_data == "?":
			# Print
			trace_log("SENSO    > Time-out")
			# Result
			return False
		# Check header
		if not frame_data.startswith("SENSO,D,"):
			# Print
			trace_log("SENSO    > Frame parse error (no header)")
			# Result
			return False
		# Try
		try:
			# Parse
			split = frame_data.split(",")
			# Reference
			self.output.timestamp = datetime.datetime.now().timestamp()
			self.output.pressure = get_pressure()
			# Extract
			if len(split) < 5:
				# Print
				trace_log(f"SENSO    > Frame parse error (bad size: {len(split)})")
				# Result
				return False
			# Store output
			self.output.channel1 = float(split[2])
			self.output.channel2 = float(split[3])
			self.output.channel3 = float(split[4])
		# Error
		except (IndexError, ValueError) as e:
			# Print
			trace_log(f"SENSO    > Frame parse error ({e})")
			# Result
			return False
		# Result
		return True

	# Acquisition process (pulsed mode)
	def _acquisition_process_pulsed_mode(self, mode: AcquisitionMode) -> bool:
		"""
			Sample acquisition process (pulsed mode)

			Returns:
				- bool: True if the acquisition process is successful
		"""
		# Power-on
		self._io_power.set_on()
		# Warm-up
		time.sleep(1.5)
		# Acquisition
		frame_data = self._serial.receive_ascii(2.0)
		# Treatment
		if self._parse_senso_frame(frame_data):
			# Print
			trace_log("SENSO    > " + f"{self.output.timestamp:.1f}" + ',' + f"{self.output.pressure:.2f}" + ',' + frame_data[8:])
			# Count success
			if mode == AcquisitionMode.PROFILE:
				self._tech.diagnosis_count_success()
			# Result
			result = True
		# Error
		else:
			# Count error
			if mode == AcquisitionMode.PROFILE:
				self._tech.diagnosis_count_error()
			# Result
			result = False
		# Count alarm
		if mode == AcquisitionMode.PROFILE:
			if not self._io_alarm.get():
				self._tech.diagnosis_count_alarm()
		# Power-off
		self._io_power.set_off()
		# Delay before new power-on (for proper operation of the sensor)
		time.sleep(0.5)
		# Result
		return result

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
		if self._acquisition_process_pulsed_mode(AcquisitionMode.DATA):
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
				- str: result string (eg: "senso   : ok", senso   : ok/error format)
		"""
		# Acquire
		if self._acquisition_process_pulsed_mode(AcquisitionMode.AUTOTEST):
			# Reply
			return "senso   : ok"
		# Error
		else:
			# Reply
			return "senso   : error"

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
		return self._acquisition_process_pulsed_mode(AcquisitionMode.PROFILE)

	# Set and share state
	def set_state(self, state):
		"""
		Set and share the state machine state

		Parameters:
			state (int): step
		"""
		# Set state
		self._step = state
		# Share with process
		self._share_step.write(state)
		# Share with web interface
		self._share_info.write(next((name for name, value in USEA_USER_STATE_MAP.items() if value == self._step), "?"))


# Create resources
senso_driver = DriverSenso(0)


# Manager
def manager(self):
	"""
		Running task
	"""

	# Trace
	trace_log("SENSO    > Activate")

	self._stop = False

	file_name = ""

	# Activate task
	self._active = True
	# Synchronize timer
	self._timer.wait_until_synchro()
	# Start timer
	self._timer.start_base_time(10.0)
	# Share
	self.set_state(self._step)

	# Loop
	while not self._stop:
		try:

			# Sensor activated ?
			if not self._active:
				time.sleep(0.1)
				continue

			# Read resources
			navigation = get_navigation()

			# Wait
			if self._step == USEA_USER_STEP_IDLE:
				# Ascent step
				if navigation == USEA_NAVIGATION_STATE_ASCENT:
					# Create file name
					file_name = "payload/" + get_profile() + "_senso.csv"
					# Print
					trace_log("SENSO    > Start acquisition")
					# Start recording
					self.set_state(USEA_USER_STEP_RECORD)
					# Reset error flags counters
					self._tech.diagnosis_reset()
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
					(navigation == USEA_NAVIGATION_STATE_ASCENT_3)):
					# Base time count
					if self._timer.is_tick():
						# Acquisition in progress
						self.set_state(USEA_USER_STEP_SAMPLE)
						# Acquire
						if self.acquire_sample():
							# Store data
							with open(file_name, "a") as file:
								file.write(
									f"{self.output.timestamp:.1f}" + ";" +
									f"{self.output.pressure:.2f}" + ";" +
									f"{self.output.channel1:.3f}" + ";" +
									f"{self.output.channel2:.3f}" + ";" +
									f"{self.output.channel3:.3f}" + "\n")
						# Acquisition finished
						self.set_state(USEA_USER_STEP_RECORD)
					# Wait
					else:
						time.sleep(0.1)
				# Other
				else:
					# Print
					trace_log("SENSO    > Stop acquisition")
					# Stop recording
					self.set_state(USEA_USER_STEP_SURFACE)

			# Surface
			elif self._step == USEA_USER_STEP_SURFACE:
				# Wait for processing
				if (
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_INCREASE) or
					(navigation == USEA_NAVIGATION_STATE_SURFACE_ACQUISITION)):
					time.sleep(0.1)
				# Treatment step
				elif navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Print
					trace_log("SENSO    > Processing")
					# Start processing
					self.set_state(USEA_USER_STEP_TREAT)
					# Save errors
					self._tech.diagnosis_save()
					# Stop processing
					self.set_state(USEA_USER_STEP_IDLE)
				# Other
				else:
					# Stop recording
					self.set_state(USEA_USER_STEP_IDLE)

			# Other
			else:
				time.sleep(0.1)

		# Stop
		except KeyboardInterrupt:
			# Trace
			trace_log("SENSO    > Deactivate")
			# Stop recording
			self.set_state(USEA_USER_STEP_IDLE)
			# Stop
			self._stop = True
			# Power-off
			self._io_power.set_off()
			# Wait
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

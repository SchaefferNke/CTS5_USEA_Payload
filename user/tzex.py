#!/bin/python
# -*- coding: utf-8 -*-
"""
	tzex.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-07-01"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import time
import traceback

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.io_lib import DriverIOOutput
from system.share_lib import FileShare, DataShare, get_navigation, get_profile, get_pressure, get_parking_timestamp, get_parking_duration, get_ctrl_action
from system.trace_lib import trace_log
from system.const import *

# Versioning
TZEX_VERSION = __version__


# Number of collection periods; excluding the final return to the neutral position
TZEX_COLLECTION_NUMBER = 2
# Minimum collection duration; deactivate acquisition if collection duration is too short (sec)
TZEX_COLLECTION_DURATION_MIN = 3600
# Hydraulic action temporal proximity; delay between hydraulic action and sample collection (sec)
TZEX_HYDRAULIC_DELAY_MIN = 600
# Speed calculation interval; delay between two consecutive pressure measurements (sec)
TZEX_SPEED_DELAY = 60
# Stability criterion; speed value to detect a stability at depth (m/sec)
TZEX_STABILITY_SPEED = 0.01
# Motor activation time; duration of a sampler action (sec)
TZEX_MOTOR_DURATION = 120
# Time reserved before the end of the parking; for the final return to the neutral position (sec)
TZEX_FINAL_RETURN_DELAY = 900


# Class definition
class DriverTZEX:
	"""
		DriverTZEX class: manage acquisition of the sampler
	"""

	# Create resource
	def __init__(self, user_index: int):
		# Manager
		self._stop = False
		self._user_index = user_index
		self._step = USEA_USER_STEP_IDLE
		self._motor_timestamp = 0.0
		self._ctrl_timestamp = 0.0
		self._last_pressure = 0.0
		self._io_power = DriverIOOutput("GPIO_3_23")
		if user_index == 0:
			self._share_step = DataShare("user_step")
			self._share_info = FileShare("user.txt")
		else:
			self._share_step = DataShare(f"user{user_index}_step")
			self._share_info = FileShare(f"user{self._user_index}.txt")

	# Get version
	# noinspection PyMethodMayBeStatic
	def get_version(self) -> str: return TZEX_VERSION

	# Dummy measurement
	def get_data(self) -> str:
		"""
			Dummy measurement

			Returns:
				- str: result string
		"""
		# Motor
		self._io_power.set_on()
		time.sleep(TZEX_MOTOR_DURATION)
		self._io_power.set_off()
		# Reply
		return "ok"

	# Get time before next activity
	def get_time_before_activity(self) -> float:
		"""
			Get the time remaining before the next activity

			Returns:
				- float: time remaining before the next activity (sec)
		"""
		# Waiting for the next measurement
		if self._step == USEA_USER_STEP_IDLE:
			result = 3600.0
		elif self._step == USEA_USER_STEP_RECORD:
			result = max(0.0, self._motor_timestamp - time.time())
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

	# Safe pressure reading
	def safe_get_pressure(self) -> float:
		"""
		Safely read pressure

		Returns:
			float: pressure value (m)
		"""
		# Read pressure
		pressure = get_pressure()
		# Integrity test; keep last pressure if reading fails
		if pressure > 0.0:
			self._last_pressure = pressure
		# Result
		return self._last_pressure

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

	# Store event in output file
	def save_output(self, file_name, info):
		"""
		Save event in output file

		Parameters:
			file_name (str): filename (eg: "001_01_tzex.csv")
			info (str): information string
		"""
		# save in output file
		with open(file_name, "a") as file:
			file.write(format_record(time.time(), self.safe_get_pressure(), info))


# Create resources
tzex_driver = DriverTZEX(0)


# Format record
def format_record(timestamp: float, pressure: float, info: str) -> str:
	"""
	Format a record
	"""
	column_formats = [
		"{:.0f}",  # Timestamp
		"{:.1f}",  # Pressure
		"{:s}"     # Info
	]
	values = [timestamp, pressure, info]
	formatted_values = [fmt.format(val) for fmt, val in zip(column_formats, values)]
	return ",".join(formatted_values) + "\n"


# Manager
def manager(self):

	# Trace
	trace_log("TZEX     > Activate")

	# Debugging purpose - Keyboard escape
	self._stop = False

	# Initialize local variables
	file_name = ""
	collection_duration = 0

	# Share
	self.set_state(self._step)

	# Loop
	while not self._stop:
		try:

			# Read resource
			navigation = get_navigation()

			# Waiting parking
			if self._step == USEA_USER_STEP_IDLE:
				# Parking stage?
				if navigation == USEA_NAVIGATION_STATE_PARK:
					# Print
					trace_log("TZEX     > Park begin")
					# Start stabilization survey
					self.set_state(USEA_USER_STEP_SURVEY)
					# Create file name
					file_name = "payload/" + get_profile() + "_tzex.csv"
					# Save in file
					self.save_output(file_name, "PARK_BEGIN")
				# Not yet in parking stage
				else:
					time.sleep(1.0)

			# Waiting for stable parking
			elif self._step == USEA_USER_STEP_SURVEY:
				# Still in parking stage?
				if navigation == USEA_NAVIGATION_STATE_PARK:
					# Parking duration test
					if get_parking_duration() < ((TZEX_COLLECTION_NUMBER * TZEX_COLLECTION_DURATION_MIN) + TZEX_FINAL_RETURN_DELAY):
						# Wait and continue
						time.sleep(1.0)
						continue
					# Read CTRL action
					ctrl_timestamp, ctrl_action = get_ctrl_action()
					# CTRL action temporal proximity test
					if (ctrl_action not in ("", "NONE")) and ((time.time() - ctrl_timestamp) < TZEX_HYDRAULIC_DELAY_MIN):
						# Save action timestamp
						self._ctrl_timestamp = ctrl_timestamp
						# Wait and continue
						time.sleep(1.0)
						continue
					# Compute current speed (m/sec)
					pressure_1 = self.safe_get_pressure()
					time.sleep(TZEX_SPEED_DELAY)
					pressure_2 = self.safe_get_pressure()
					speed = (pressure_2 - pressure_1) / float(TZEX_SPEED_DELAY)
					# Stable at depth?
					if -TZEX_STABILITY_SPEED < speed < TZEX_STABILITY_SPEED:
						# Print
						trace_log("TZEX     > Stability criterion")
						# Start recording
						self.set_state(USEA_USER_STEP_RECORD)
						# Compute remaining time
						remaining_time = max(0.0, get_parking_duration() - (time.time() - get_parking_timestamp()))
						# Compute collection duration
						collection_duration = (remaining_time - TZEX_FINAL_RETURN_DELAY) / TZEX_COLLECTION_NUMBER
						# Activate motor immediately
						self._motor_timestamp = time.time()
						# Save in file
						self.save_output(file_name, "PARK_STABILITY")
					# Not yet stable at depth
					else:
						time.sleep(1.0)
				# No longer in parking stage
				else:
					# Print
					trace_log("TZEX     > Park end")
					# Stop recording
					self.set_state(USEA_USER_STEP_IDLE)
					# Save in file
					self.save_output(file_name, "PARK_END")

			# Collecting
			elif self._step == USEA_USER_STEP_RECORD:
				# Still in parking stage?
				if navigation == USEA_NAVIGATION_STATE_PARK:
					# Read CTRL action
					ctrl_timestamp, ctrl_action = get_ctrl_action()
					# New CTRL action?
					if (ctrl_action not in ("", "NONE")) and (ctrl_timestamp > self._ctrl_timestamp):
						# Save action timestamp
						self._ctrl_timestamp = ctrl_timestamp
						# Save in file
						self.save_output(file_name, ctrl_action)
					# CTRL temporal proximity test
					if (ctrl_action not in ("", "NONE")) and ((time.time() - ctrl_timestamp) < TZEX_HYDRAULIC_DELAY_MIN):
						# Wait and continue
						time.sleep(1.0)
						continue
					# Time to take a sample?
					if time.time() >= self._motor_timestamp:
						# Compute next motor activation
						self._motor_timestamp += collection_duration
						# Print
						trace_log("TZEX     > Motor on")
						# Start rotating
						self.set_state(USEA_USER_STEP_SAMPLE)
						# Save in file
						self.save_output(file_name, "MOTOR_ON")
						# Motor
						self._io_power.set_on()
						time.sleep(TZEX_MOTOR_DURATION)
						self._io_power.set_off()
						# Print
						trace_log("TZEX     > Motor off")
						# Stop rotating
						self.set_state(USEA_USER_STEP_RECORD)
						# Save in file
						self.save_output(file_name, "MOTOR_OFF")
					# Wait
					else:
						time.sleep(1.0)
				# No longer in parking stage
				else:
					# Print
					trace_log("TZEX     > Park end")
					# Stop recording
					self.set_state(USEA_USER_STEP_IDLE)
					# Save in file
					self.save_output(file_name, "PARK_END")

			# Other
			else:
				time.sleep(1.0)

		# Manual exit
		except KeyboardInterrupt:
			# Trace
			trace_log("TZEX     > Deactivate")
			# Stop
			self._stop = True
			# Power-off
			self._io_power.set_off()
			# Wait
			time.sleep(0.1)

		# Error
		except Exception as err:
			# Power-off
			self._io_power.set_off()
			# Stop recording
			self.set_state(USEA_USER_STEP_IDLE)
			# Trace
			print(err)
			print(traceback.format_exc())
			# Trace
			trace_log("TZEX     > [ERROR]")


# Test function
if __name__ == "__main__":
	# Run
	tzex_driver.run()

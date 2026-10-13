#!/bin/python
# -*- coding: utf-8 -*-
"""
	stream.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-10-07"
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
from system.serial_lib import DriverSerial
from system.timer_lib import DriverTimer
from system.trace_lib import trace_log

# Versioning
STREAM_VERSION = __version__


# Class definition
class DataStream:
	"""
		DataStream class: sensor data

		Attributes:
			- string (str): sensor output stream
	"""
	# Output
	def __init__(self):
		self.timestamp = 0.0
		self.string = ''


# Class definition
class DriverStream:
	"""
		DriverStream class: manage acquisition of sensor
	"""

	# Create resource
	def __init__(self, user_index: int):
		# Manager
		self._stop = False
		self._user_index = user_index
		self._io_power = DriverIOOutput("GPIO_3_20")
		self._serial = DriverSerial("COM_5", 19200, 0.5)
		self._timer = DriverTimer("stream")
		# Output
		self.output = DataStream()

	# Acquisition
	def _acquisition(self) -> bool:
		"""
			Sample acquisition

			Returns:
				- bool: True if the acquisition process is successful
		"""
		# Power-on
		self._io_power.set_on()
		# Acquisition
		frame_data = self._serial.receive_ascii(2.5)
		# Error
		if not frame_data or frame_data == "?":
			# Result
			result = False
		# Treatment
		else:
			# Reference
			self.output.timestamp = time.time()
			# Output
			self.output.string = frame_data
			# Print
			trace_log("STREAM   > " + f"{self.output.timestamp:.1f}" + ',' + frame_data)
			# Result
			result = True
		# Power-off
		self._io_power.set_off()
		# Result
		return result

	# Get version
	# noinspection PyMethodMayBeStatic
	def get_version(self) -> str: return STREAM_VERSION

	# Dummy measurement
	def get_data(self) -> str:
		"""
			Dummy measurement

			Returns:
				- str: result string ("no reply" if error)
		"""
		# Acquire
		if self._acquisition():
			# Reply
			return self.output.string
		# Error
		else:
			# Reply
			return "no reply"

	# Get time before next activity
	def get_time_before_activity(self) -> float:
		"""
			Get the time remaining before the next activity

			Returns:
				- float: time remaining before the next activity (sec)
		"""
		# Waiting for the next measurement
		result = self._timer.remaining_time()
		# Result
		return result

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Scheduler
		steam_manager(self)


# Create resources
stream_driver = DriverStream(0)


# Manager
def steam_manager(self):
	"""
		Running task
	"""

	# Trace
	trace_log("STREAM   > Activate")

	# Debugging purpose - Keyboard escape
	self._stop = False

	# Start timer
	self._timer.start_base_time(5.0)

	# Loop
	while not self._stop:
		try:

			# Base time count
			if self._timer.is_tick():
				# Acquire
				if self._acquisition():
					# Store data
					with open("payload/stream.txt", "a") as file:
						file.write(f"{self.output.timestamp:.1f}" + ',' + self.output.string + '\r\n')
				# Error
				else:
					# Trace
					trace_log("STREAM   > Time-out")
			# Wait
			else:
				time.sleep(0.1)

		# Stop
		except KeyboardInterrupt:
			# Trace
			trace_log("STREAM   > Deactivate")
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
			trace_log("STREAM   > [ERROR]")


# Test function
if __name__ == "__main__":
	# Run
	stream_driver.run()

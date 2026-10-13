#!/bin/python
# -*- coding: utf-8 -*-
"""
	dummy.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-08-24"
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
from system.share_lib import FileShare, DataShare
from system.trace_lib import trace_log
from system.const import *

# Versioning
DUMMY_VERSION = __version__


# Class definition
class DriverDummy:
	"""
		DriverDummy class: manage dummy driver
	"""

	# Create resource
	def __init__(self, user_index: int):
		# Manager
		self._stop = False
		self._user_index = user_index
		self._step = USEA_USER_STEP_IDLE
		if user_index == 0:
			self._share_step = DataShare("user_step")
			self._share_info = FileShare("user.txt")
		else:
			self._share_step = DataShare(f"user{user_index}_step")
			self._share_info = FileShare(f"user{self._user_index}.txt")

	# Get version
	# noinspection PyMethodMayBeStatic
	def get_version(self) -> str: return DUMMY_VERSION

	# Dummy measurement
	# noinspection PyMethodMayBeStatic
	def get_data(self) -> str: return "ok"

	# Test sensor
	# noinspection PyMethodMayBeStatic
	def test(self) -> str: return "dummy   : ok"

	# Get time before next activity
	# noinspection PyMethodMayBeStatic
	def get_time_before_activity(self) -> float: return 3600.0

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Scheduler
		manager(self)

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
dummy_driver = DriverDummy(0)


# Manager
def manager(self):

	# Trace
	trace_log("DUMMY    > Activate")

	# Debugging purpose - Keyboard escape
	self._stop = False

	# Share
	self.set_state(self._step)

	# Loop
	while not self._stop:
		try:
			# Do nothing
			time.sleep(1.0)

		# Manual exit
		except KeyboardInterrupt:
			# Trace
			trace_log("DUMMY    > Deactivate")
			# Stop
			self._stop = True
			# Wait
			time.sleep(0.1)

		# Error
		except Exception as err:
			# Trace
			print(err)
			print(traceback.format_exc())
			# Trace
			trace_log("DUMMY    > [ERROR]")


# Test function
if __name__ == "__main__":
	# Run
	dummy_driver.run()

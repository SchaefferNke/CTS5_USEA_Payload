#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	ctd.py
	"""

# Standard libraries
import sys
import traceback

# Project libraries
from system.timer_lib import *
from system.share_lib import *


# Output definition
class DriverCtdContent:
	"""
		DataCtd class: CTD sample

		Attributes:
			- timestamp (float): timestamp (Unix Epoch)
			- pressure (float): pressure value (dbar)
			- temperature (float): temperature value (degC)
			- salinity (float): salinity value (PSU)
		"""

	# Output
	def __init__(self):
		self.timestamp = 0.0
		self.pressure = 0.0
		self.temperature = 0.0
		self.salinity = 0.0


# Class definition
class DriverCtd:
	"""
		DriverCtd class: store and share CTD triplet
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.timer = DriverTimer(path, "ctd")
		self.share_data = FileShare(path, "ctd.txt")
		# Output
		self.output = DriverCtdContent()
		self.output.timestamp = 0.0
		self.output.pressure = 0.0
		self.output.temperature = 0.0
		self.output.salinity = 0.0

	# Get next task activity
	def time_before_activity(self) -> float:
		"""
			Get the time remaining before the next task activity

			Returns:
				- float: time remaining before the next task activity (sec)
			"""
		# Waiting for the next measurement
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
ctd_driver = DriverCtd()


# Manager
def manager(self):
	global path

	# Trace
	trace_log(path, "CTD      > Activate")

	# Start timer
	self.timer.start_base_time(1.0)

	# Loop
	try:
		while True:

			# Acquisition rate
			if not self.timer.is_tick():
				time.sleep(0.1)
				continue

			# Read resource
			self.share_data.read()

			# New ctd sample
			if self.share_data.content.timestamp > self.output.timestamp:
				# Parse
				split = self.share_data.content.string.split(",")
				# Extract
				self.output.timestamp = self.share_data.content.timestamp
				self.output.pressure = float(split[0])
				self.output.temperature = float(split[1])
				self.output.salinity = float(split[2])
				# Store data
				file = open(path + "ctd/" + get_profile(path) + "_ctd.csv", "a+")
				file.write(
					f"{self.output.timestamp:.3f}" + "," +
					f"{self.output.pressure:.2f}" + "," +
					f"{self.output.temperature:.3f}" + "," +
					f"{self.output.salinity:.3f}" + "\n")
				file.close()

			# Wait
			else:
				time.sleep(0.1)

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log(path, "CTD      > [ERROR]")


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
	ctd = DriverCtd()
	# Run
	ctd.run()

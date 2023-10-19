#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	ctd.py
	"""

# Standard libraries
import sys
import time
import traceback

# Project libraries
from system.share_lib import *
from system.trace_lib import *


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
		self.share_data = FileShare(path, "ctd.txt")
		# Output
		self.output = DriverCtdContent()
		self.output.timestamp = 0.0
		self.output.pressure = 0.0
		self.output.temperature = 0.0
		self.output.salinity = 0.0

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

	# Loop
	try:
		while True:

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

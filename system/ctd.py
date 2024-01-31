#!/bin/python
# -*- coding: utf-8 -*-
"""
	ctd.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-01-31"
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
from system.share_lib import FileShare, get_profile
from system.trace_lib import trace_log


# Class definition
class DataCTD:
	"""
		DataCTD class: CTD data

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
class DriverCTD:
	"""
		DriverCTD class: store and share CTD triplet
	"""

	# Create resource
	def __init__(self):
		# Manager
		self._share_data = FileShare("ctd.txt")
		# Output
		self.output = DataCTD()
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
ctd_driver = DriverCTD()


# Manager
def manager(self):
	"""
		Running task
	"""

	# Trace
	trace_log("CTD      > Activate")

	# Loop
	try:
		while True:

			# Read resource
			self._share_data.read()

			# New ctd sample
			if self._share_data.content.timestamp > self.output.timestamp:
				# Parse
				split = self._share_data.content.string.split(",")
				# Extract
				self.output.timestamp = self._share_data.content.timestamp
				self.output.pressure = float(split[0])
				self.output.temperature = float(split[1])
				self.output.salinity = float(split[2])
				# Store data
				file = open("ctd/" + get_profile() + "_ctd.csv", "a+")
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
		trace_log("CTD      > [ERROR]")


# Test function
if __name__ == "__main__":
	# Run
	ctd_driver.run()

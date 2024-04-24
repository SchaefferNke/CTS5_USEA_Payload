#!/bin/python
# -*- coding: utf-8 -*-
"""
	share_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-04-24"
__version__ = "1.0.0"

# Standard libraries
import os
import datetime
import threading

# Project libraries
from system.const import *

# Event list
events = {}


# Class definition
class EventShare:
	"""
		EventShare class: share an event between tasks

		Attributes:
			- name (str): event name

		Operations:
			- Binary semaphore used for synchronization purpose
	"""

	# Create resource
	def __init__(self, name: str):
		# Manager
		self._name = name
		if not name in events:
			events[name] = threading.Event()

	# Set event
	def set(self):
		"""
			Set the event
		"""
		# Set
		events[self._name].set()

	# Reset event
	def reset(self):
		"""
			Clear the event
		"""
		# Reset
		events[self._name].clear()

	# Test event
	def is_set(self):
		"""
			Test the event state

			Returns:
				- bool: True if the event is set
		"""
		# Test
		return events[self._name].is_set()

	# Wait event
	def wait(self):
		"""
			Wait until the event is set
		"""
		# Wait
		events[self._name].wait()


# Lock list
var_locks = {}


# File record definition
class DataShareContent:
	"""
		DataShareContent class: shared variable

		Attributes:
			- value (object): variable object
	"""

	# Variable
	def __init__(self):
		self.value = 0


# Class definition
class DataShare:
	"""
		DataShare class: share a variable between tasks

		Attributes:
			- name (str): variable name

		Operations:
			- Binary semaphore used for mutual exclusion on a resource variable
	"""

	# Variable
	variable = DataShareContent()

	# Create resource
	def __init__(self, name: str):
		# Manager
		self._name = name
		if not name in var_locks:
			var_locks[name] = threading.Lock()

	# Read resource
	def read(self) -> object:
		"""
			Read a variable

			Returns:
				- object: data object
		"""
		# Wait for resource
		if not var_locks[self._name].acquire(timeout=60.0):
			# Result
			return 0
		# Read value
		value = self.variable.value
		# Release resource
		var_locks[self._name].release()
		# Result
		return value

	# Write resource
	def write(self, value: object):
		"""
			Write a variable

			Parameters:
				- value (object): data object
		"""
		# Wait for resource
		var_locks[self._name].acquire()
		# Write value
		self.variable.value = value
		# Release resource
		var_locks[self._name].release()


# Lock list
file_locks = {}


# File record definition
class FileShareContent:
	"""
		FileShareContent class: shared file

		Attributes:
			- timestamp (str): Unix Epoch timestamp
			- string (str): event
	"""

	# File content
	def __init__(self):
		self.timestamp = 0.0
		self.string = ""


# Class definition
class FileShare:
	"""
		FileShare class: share a file between tasks

		Attributes:
			- filename (str): file name

		Operations:
			- Binary semaphore used for mutual exclusion on a resource file
	"""

	# Create resource
	def __init__(self, filename: str):
		# Manager
		self._filename = filename
		if not filename in file_locks:
			file_locks[filename] = threading.Lock()
		# File content
		self.content = FileShareContent()
		self.content.timestamp = 0.0
		self.content.string = ""

	# Read resource file
	def read(self) -> object:
		"""
			Read from file

			Returns:
				- object: content (timestamp and string)
		"""
		# Resource doesn't exist
		if not os.path.isfile("share/" + self._filename):
			# Fill empty content
			self.content.timestamp = 0.0
			self.content.string = "?"
			# Result
			return str(self.content)
		# Wait for resource
		if not file_locks[self._filename].acquire(timeout=60.0):
			# Fill empty content
			self.content.timestamp = 0.0
			self.content.string = "?"
			# Result
			return str(self.content)
		# Read file
		file = open("share/" + self._filename, "r")
		info = file.read()
		file.close()
		# Parse
		split = info.split(";")
		# Extract
		self.content.timestamp = float(split[0])
		self.content.string = split[1]
		# Release resource
		file_locks[self._filename].release()
		# Result
		return str(self.content)

	# Write resource file
	def write(self, info: str):
		"""
			Write in file

			Parameters:
				- info (str): string to write
		"""
		# Wait for resource
		file_locks[self._filename].acquire()
		# Timestamp
		now = datetime.datetime.now()
		# Write file
		file = open("share/" + self._filename, "w")
		file.write(f"{now.timestamp():.3f}" + ";" + info)
		file.close()
		# Release resource
		file_locks[self._filename].release()


# Get current profile
def get_profile() -> str:
	"""
		Read profile identification string

		Returns:
			- str: profile identification string (eg: "003_01", "CCC_PP" format)
	"""
	# Create resource
	share = FileShare("profile.txt")
	# Read resource
	share.read()
	# Result
	return share.content.string


# Get current navigation stage
def get_navigation() -> int:
	"""
		Read navigation identification string

		Returns:
			- int: navigation identification value (see const.py)
	"""
	# Create resource
	share = FileShare("navigation.txt")
	# Read resource
	share.read()
	# Result
	if share.content.string == "NA":
		return USEA_NAVIGATION_STATE_BUOYANCY_DECREASE
	elif share.content.string == "NB":
		return USEA_NAVIGATION_STATE_DESCENT
	elif share.content.string == "NC":
		return USEA_NAVIGATION_STATE_PARK
	elif share.content.string == "ND":
		return USEA_NAVIGATION_STATE_DEEP_DESCENT
	elif share.content.string == "NE":
		return USEA_NAVIGATION_STATE_DEEP_PARK
	elif share.content.string == "NF":
		return USEA_NAVIGATION_STATE_ASCENT
	elif share.content.string == "NG":
		return USEA_NAVIGATION_STATE_SUB_SURFACE
	elif share.content.string == "NH":
		return USEA_NAVIGATION_STATE_BUOYANCY_INCREASE
	elif share.content.string == "NI":
		return USEA_NAVIGATION_STATE_RESCUE
	elif share.content.string == "NJ":
		return USEA_NAVIGATION_STATE_ASCENT_1
	elif share.content.string == "NK":
		return USEA_NAVIGATION_STATE_ASCENT_2
	elif share.content.string == "NL":
		return USEA_NAVIGATION_STATE_ASCENT_3
	elif share.content.string == "SB":
		return USEA_NAVIGATION_STATE_GPS
	elif share.content.string == "SC":
		return USEA_NAVIGATION_STATE_RUDICS
	elif share.content.string == "SF":
		return USEA_NAVIGATION_STATE_SURFACE_ACQUISITION
	elif share.content.string == "TC":
		return USEA_NAVIGATION_STATE_DATA_PROCESSING
	elif share.content.string == "FN":
		return USEA_NAVIGATION_STATE_END_OF_LIFE
	else:
		return USEA_NAVIGATION_STATE_UNDEFINED


# Get current pressure
def get_pressure() -> float:
	"""
		Read last pressure value

		Returns:
			- float: pressure value (dbar)
	"""
	# Create resource
	share = FileShare("pressure.txt")
	# Read resource
	share.read()
	# Result
	return float(share.content.string)

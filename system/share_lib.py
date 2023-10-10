#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	share_lib.py
	"""

# Standard libraries
import datetime
import threading

# Project libraries
from system.const import *

# Event list
events = {}


# Class definition
class EventShare:
	"""
		EventShare class
		"""

	# Create resource
	def __init__(self, name: str):
		# Manager
		self.name = name
		if not name in events:
			events[name] = threading.Event()

	# Set event
	def set(self):
		"""
			Set the event
			"""
		# Set
		events[self.name].set()

	# Reset event
	def reset(self):
		"""
			Clear the event
			"""
		# Reset
		events[self.name].clear()

	# Test event
	def is_set(self):
		"""
			Test the event state

			Returns:
				bool: True if the event is set
			"""
		# Test
		return events[self.name].is_set()

	# Wait event
	def wait(self):
		"""
			Wait until the event is set
			"""
		# Wait
		events[self.name].wait()


# Lock list
var_locks = {}


# File record definition
class DataValue:

	# Variable
	def __init__(self):
		self.value = 0


# Class definition
class DataShare:
	"""
		DataShare class
		"""

	# Variable
	var = DataValue()

	# Create resource
	def __init__(self, name: str):
		# Manager
		self.name = name
		if not name in var_locks:
			var_locks[name] = threading.Lock()

	# Read resource
	def read(self) -> object:
		"""
			Read a data

			Returns:
				object: data object
			"""
		# Wait for resource
		var_locks[self.name].acquire()
		# Read value
		value = self.var.value
		# Release resource
		var_locks[self.name].release()
		# Result
		return value

	# Write resource
	def write(self, value: object):
		"""
			Write a data

			Parameters:
				value (object): data object
			"""
		# Wait for resource
		var_locks[self.name].acquire()
		# Write value
		self.var.value = value
		# Release resource
		var_locks[self.name].release()


# Lock list
file_locks = {}


# File record definition
class DataFile:

	# File content
	def __init__(self):
		self.timestamp = 0.0
		self.string = ""


# Class definition
class FileShare:
	"""
		FileShare class
		"""

	# Create resource
	def __init__(self, path: str, filename: str):
		# Manager
		self.path = path
		self.filename = filename
		if not filename in file_locks:
			file_locks[filename] = threading.Lock()
		# File content
		self.content = DataFile()
		self.content.timestamp = 0.0
		self.content.string = ""

	# Read resource file
	def read(self) -> str:
		"""
			Read from file

			Returns:
				str: content string without timestamp
			"""
		# Wait for resource
		file_locks[self.filename].acquire()
		# Read file
		file = open(self.path + "share/" + self.filename, "r")
		info = file.read()
		file.close()
		# Parse
		split = info.split(";")
		# Extract
		self.content.timestamp = float(split[0])
		self.content.string = split[1]
		# Release resource
		file_locks[self.filename].release()
		# Result
		return str(self.content)

	# Write resource file
	def write(self, info: str):
		"""
			Write into file

			Parameters:
				info (str): string to write
			"""
		# Wait for resource
		file_locks[self.filename].acquire()
		# Timestamp
		now = datetime.datetime.now()
		# Write file
		file = open(self.path + "share/" + self.filename, "w")
		file.write(f"{now.timestamp():.3f}" + ";" + info)
		file.close()
		# Release resource
		file_locks[self.filename].release()


# Get current profile
def get_profile(path: str) -> str:
	"""
		Read profile identification string

		Returns:
			str: profile identification string in "CCC_PP" format
		"""
	# Create resource
	share = FileShare(path, "profile.txt")
	# Read resource
	share.read()
	# Result
	return share.content.string


# Get current navigation stage
def get_navigation(path: str) -> int:
	"""
		Read navigation identification string

		Returns:
			str: navigation identification string in "XX" format
		"""
	# Create resource
	share = FileShare(path, "navigation.txt")
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
def get_pressure(path: str) -> float:
	"""
		Read last pressure value

		Returns:
			float: pressure value (dbar)
		"""
	# Create resource
	share = FileShare(path, "pressure.txt")
	# Read resource
	share.read()
	# Result
	return float(share.content.string)

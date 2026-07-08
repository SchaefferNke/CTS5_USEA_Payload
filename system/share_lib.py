#!/bin/python
# -*- coding: utf-8 -*-
"""
	share_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-07-03"
__version__ = "1.0.2"

# Standard libraries
import os
import time
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
		if not self._name in events:
			events[self._name] = threading.Event()

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

	# Wait event
	def wait_timeout(self, timeout: float) -> bool:
		"""
			Wait until the event is set

			Attributes:
				- timeout (float): timeout value

			Returns:
				- bool: False in case of timeout
		"""
		# Wait
		return events[self._name].wait(timeout=timeout)


# Lock list
var_locks = {}
# Value list
var_value = {}


# Class definition
class DataShare:
	"""
		DataShare class: share a variable between tasks

		Attributes:
			- name (str): variable name

		Operations:
			- Binary semaphore used for mutual exclusion on a resource variable
	"""

	# Create resource
	def __init__(self, name: str):
		# Manager
		self._name = name
		if not name in var_locks:
			var_locks[self._name] = threading.Lock()
		# Value
		if self._name not in var_value:
			var_value[self._name] = -1

	# Read resource
	def read(self, timeout: float | None = None) -> object:
		"""
			Read a variable

			Parameters:
				- timeout (float): timeout value

			Returns:
				- object: data object
		"""
		# Optional timeout
		if timeout is None:
			timeout = 60.0
		# Select lock
		lock = var_locks[self._name]
		# Wait for resource
		acquired = lock.acquire(timeout=timeout)
		# Timeout
		if not acquired:
			# Result
			return -1
		# Read value
		try:
			# Result
			return var_value[self._name]
		# Release resource
		finally:
			lock.release()

	# Write resource
	def write(self, value: object, timeout: float | None = None) -> bool:
		"""
			Write a variable

			Parameters:
				- value (object): data object
				- timeout (float): timeout value

			Returns:
				- bool: False in case of timeout
		"""
		# Optional timeout
		if timeout is None:
			timeout = 60.0
		# Select lock
		lock = var_locks[self._name]
		# Wait for resource
		acquired = lock.acquire(timeout=timeout)
		# Timeout
		if not acquired:
			# Error
			return False
		# Try
		try:
			# Write
			var_value[self._name] = value
			# Ok
			return True
		# Release resource
		finally:
			lock.release()


# Lock list
file_locks = {}


# File record definition
class FileShareContent:
	"""
		FileShareContent class: shared file

		Attributes:
			- timestamp (float): Unix Epoch timestamp
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
		if not self._filename in file_locks:
			file_locks[self._filename] = threading.Lock()
		# File content
		self.content = FileShareContent()
		self.content.timestamp = 0.0
		self.content.string = ""

	# Read resource file
	def read(self, timeout: float | None = None) -> object:
		"""
			Read from file

			Parameters:
				- timeout (float): timeout value

			Returns:
				- object: content (timestamp and string)
		"""
		# Optional timeout
		if timeout is None:
			timeout = 60.0
		# Resource doesn't exist
		if not os.path.exists("share/" + self._filename):
			# Fill empty content
			self.content.timestamp = 0.0
			self.content.string = "?"
			# Result
			return str(self.content)
		# Wait for resource
		if not file_locks[self._filename].acquire(timeout=timeout):
			# Fill empty content
			self.content.timestamp = 0.0
			self.content.string = "?"
			# Result
			return str(self.content)
		# Read file
		try:
			with open("share/" + self._filename, "r") as file:
				info = file.read()
		# Release resource
		finally:
			file_locks[self._filename].release()
		# Parse
		split = info.split(";", 1)
		# Verify
		if not len(split) == 2:
			# Print
			print(info)
			# Fill empty content
			self.content.timestamp = 0.0
			self.content.string = "?"
			# Result
			return str(self.content)
		# Extract
		self.content.timestamp = float(split[0])
		self.content.string = split[1]
		# Result
		return str(self.content)

	# Write resource file
	def write(self, info: str, timeout: float | None = None) -> bool:
		"""
			Write in file

			Parameters:
				- info (str): string to write
				- timeout (float): timeout value

			Returns:
				- bool: False in case of timeout
		"""
		# Optional timeout
		if timeout is None:
			timeout = 60.0
		# Wait for resource
		acquired = file_locks[self._filename].acquire(timeout=timeout)
		# Timeout
		if not acquired:
			return False
		# Try
		try:
			# Write file
			with open("share/" + self._filename, "w") as file:
				file.write(f"{time.time():.3f}" + ";" + info)
		# Release resource
		finally:
			file_locks[self._filename].release()
		# Result
		return True

	# Lock resource file
	def lock(self, timeout: float | None = None) -> bool:
		"""
			Lock file

			Parameters:
				- timeout (float): timeout value

			Returns:
				- bool: False in case of timeout
		"""
		# Optional timeout
		if timeout is None:
			timeout = 60.0
		# Wait for resource
		return file_locks[self._filename].acquire(timeout=timeout)

	# Unlock resource file
	def unlock(self):
		"""
			Unlock file
		"""
		# Select resource
		lock = file_locks[self._filename]
		# Release resource
		if lock.locked():
			lock.release()


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
	nav_code = share.content.string
	return USEA_NAVIGATION_MAP_1.get(nav_code, USEA_NAVIGATION_STATE_UNDEFINED)


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
	# Integrity test
	if share.content.string == "?":
		return 0.0
	# Result
	try:
		return float(share.content.string)
	except ValueError:
		return 0.0


# Get parking timestamp
def get_parking_timestamp() -> float:
	"""
		Read parking starting date

		Returns:
			- float: timestamp
	"""
	# Create resource
	share = FileShare("parking.txt")
	# Read resource
	share.read()
	# Result
	try:
		return float(share.content.timestamp)
	except (ValueError, TypeError):
		return 0.0


# Get parking pressure
def get_parking_pressure() -> int:
	"""
		Read parking target pressure

		Returns:
			- int: pressure value (dbar)
	"""
	# Create resource
	share = FileShare("parking.txt")
	# Read resource
	share.read()
	# Integrity test
	if share.content.string in ("", "?"):
		return 0
	# Result
	try:
		return int(share.content.string.split(",")[0])
	except ValueError:
		return 0


# Get parking duration
def get_parking_duration() -> int:
	"""
		Read parking duration

		Returns:
			- int: duration time (sec)
	"""
	# Create resource
	share = FileShare("parking.txt")
	# Read resource
	share.read()
	# Integrity test
	if share.content.string in ("", "?"):
		return 0
	# Result
	try:
		return int(share.content.string.split(",")[1])
	except ValueError:
		return 0


# Get control action
def get_ctrl_action() -> tuple[float, str]:
	"""
		Read parking duration

		Returns:
			- float: timestamp
			- str: action (eg: "PUMP")
	"""
	# Create resource
	share = FileShare("ctrl.txt")
	# Read resource
	share.read()
	# Integrity test
	if share.content.string in ("", "?"):
		return 0.0, "NONE"
	# Result
	try:
		return share.content.timestamp, share.content.string
	except ValueError:
		return 0.0, "NONE"

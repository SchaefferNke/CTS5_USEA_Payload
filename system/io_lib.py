#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	io_lib.py
	"""

# Standard libraries
import threading

# Lock list
io_locks = {}


# Class definition
class DriverIO:
	"""
		DriverIO class
		"""

	# Create resource
	def __init__(self, name: str):
		# Manager
		self.name = name
		self.is_on = False
		if not name in io_locks:
			io_locks[name] = threading.Lock()

	# Set output on
	def set_on(self):
		"""
			Set the output on
			"""
		# Wait for resource
		io_locks[self.name].acquire()
		# Set output on
		# ...
		# Save state
		self.is_on = True
		# Release resource
		io_locks[self.name].release()

	# Set output off
	def set_off(self):
		"""
			Set the output off
			"""
		# Wait for resource
		io_locks[self.name].acquire()
		# Set output off
		# ...
		# Save state
		self.is_on = False
		# Release resource
		io_locks[self.name].release()

	# Test output state
	def is_on(self) -> bool:
		"""
			Test the output state

			Returns:
				bool: True if the output is on
			"""
		# Wait for resource
		io_locks[self.name].acquire()
		# Test
		result = self.is_on
		# Release resource
		io_locks[self.name].release()
		# Result
		return result

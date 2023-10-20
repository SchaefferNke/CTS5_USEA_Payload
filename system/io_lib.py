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
class DriverIOOutput:
	"""
		DriverIOOutput class: outputs resources access for tasks

		Attributes:
			- name (str): IO name
		"""

	# Create resource
	# TODO: ajouter paramètre d'accès GPIO
	def __init__(self, name: str):
		# Manager
		self.name = name
		self.is_on = False
		# TODO: configurer en sortie
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
		# TODO: ...
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
		# TODO: ...
		# Save state
		self.is_on = False
		# Release resource
		io_locks[self.name].release()

	# Test output state
	def is_on(self) -> bool:
		"""
			Test the output state

			Returns:
				- bool: True if the output is on
			"""
		# Wait for resource
		io_locks[self.name].acquire()
		# Test
		result = self.is_on
		# Release resource
		io_locks[self.name].release()
		# Result
		return result


# Class definition
class DriverIOInput:
	"""
		DriverIOInput class: inputs resources access for tasks

		Attributes:
			- name (str): IO name
		"""

	# Create resource
	# TODO: ajouter paramètre d'accès GPIO
	def __init__(self, name: str):
		# Manager
		self.name = name
		# TODO: configurer en entrée
		if not name in io_locks:
			io_locks[name] = threading.Lock()

	# Test input state
	def is_on(self) -> bool:
		"""
			Test the input state

			Returns:
				- bool: True if the input is on
			"""
		# Wait for resource
		io_locks[self.name].acquire()
		# Test
		# TODO: result = ...
		# Release resource
		io_locks[self.name].release()
		# Result
		return result

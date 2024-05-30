#!/bin/python
# -*- coding: utf-8 -*-
"""
	io_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-05-30"
__version__ = "1.0.0"

# Standard libraries
import threading

# Project libraries
from system.system_lib import system_driver

# Lock list
io_locks = {}


# Class definition
class DriverIOOutput:
	"""
		DriverIOOutput class: outputs resources access for tasks

		Attributes:
			- name (str): IO name (eg: "GPIO_3_8")
	"""

	# Create resource
	def __init__(self, name: str):
		# Manager
		self._name = system_driver.format_gpio_name(name)
		self._is_on = False
		if not self._name in io_locks:
			io_locks[self._name] = threading.Lock()

	# Set output on
	def set_on(self):
		"""
			Set the output on
		"""
		# Wait for resource
		io_locks[self._name].acquire()
		# Set output on
		system_driver.output_set_on(self._name)
		# Save state
		self._is_on = True
		# Release resource
		io_locks[self._name].release()

	# Set output off
	def set_off(self):
		"""
			Set the output off
		"""
		# Wait for resource
		io_locks[self._name].acquire()
		# Set output off
		system_driver.output_set_off(self._name)
		# Save state
		self._is_on = False
		# Release resource
		io_locks[self._name].release()

	# Test output state
	def is_on(self) -> bool:
		"""
			Test the output state

			Returns:
				- bool: True if the output is on
		"""
		# Wait for resource
		io_locks[self._name].acquire()
		# Test
		result = self._is_on
		# Release resource
		io_locks[self._name].release()
		# Result
		return result


# Class definition
class DriverIOInput:
	"""
		DriverIOInput class: inputs resources access for tasks

		Attributes:
			- name (str): IO name (eg: "GPIO_3_4")
	"""

	# Create resource
	def __init__(self, name: str):
		# Manager
		self._name = system_driver.format_gpio_name(name)
		if not self._name in io_locks:
			io_locks[self._name] = threading.Lock()

	# Test input state
	def is_on(self) -> bool:
		"""
			Test the input state

			Returns:
				- bool: True if the input is on
		"""
		# Wait for resource
		io_locks[self._name].acquire()
		# Read
		result = system_driver.input_is_on(self._name)
		# Release resource
		io_locks[self._name].release()
		# Result
		return result

#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	io_lib.py
	"""

# Standard libraries
import os
import threading

# Lock list
io_locks = {}


# Generate GPIO string for system command
def io_name_to_gpio_name(name: str) -> str:
	"""
		Translates IO name into system GPIO name

		Parameters:
			- name (str): IO name (eg: GPIO_3_8)

		Returns:
			- str: GPIO name for system access (eg: gpiochip3 8)
		"""
	# Format
	split = name.split("_")
	result = "gpiochip" + str(int(split[1])-1) + " " + split[2]
	# Result
	return result


# Class definition
class DriverIOOutput:
	"""
		DriverIOOutput class: outputs resources access for tasks

		Attributes:
			- name (str): IO name (eg: GPIO_3_8)
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
		if not os.name == "nt":
			os.system("gpioset " + io_name_to_gpio_name(self.name) + "=1")
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
		if not os.name == "nt":
			os.system("gpioset " + io_name_to_gpio_name(self.name) + "=0")
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
			- name (str): IO name (eg: GPIO_3_4)
		"""

	# Create resource
	def __init__(self, name: str):
		# Manager
		self.name = name
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
		if not os.name == "nt":
			result = os.system("gpioget " + io_name_to_gpio_name(self.name))
		else:
			result = "0"
		# Release resource
		io_locks[self.name].release()
		# Result
		if result == "1":
			return True
		return False

#!/bin/python
# -*- coding: utf-8 -*-
"""
	config.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-05-07"
__version__ = "1.0.0"

# Standard libraries
import sys
import time
from configparser import RawConfigParser
# import traceback


# Read user configuration field
def read_configuration(section: str, field: str) -> str:
	"""
		Read user configuration field

		Parameters:
			- section (str): section string
			- field (str): field string

		Returns:
			- str: field value
	"""
	try:
		# Read config
		config = RawConfigParser()
		config.read("./user/user.ini")
		# Result
		return config.get(section, field)

	except Exception as err:
		# Result
		return "undefined"


# Load user class
def load_class(source_code: str, class_name: str, default_class):
	"""
		Load user class

		Parameters:
			- source_code (str): source code string
			- class_name (str): class name string
			- default_class (class): default class

		Returns:
			- class: user class
	"""
	try:
		# Load module
		sys.path.insert(1, "./user")
		user_module = __import__(source_code.split(".")[0])
		# Result
		return getattr(user_module, class_name, default_class)

	except Exception as err:
		# Trace
		# print(err)
		# print(traceback.format_exc())
		# Result
		return default_class


# Load user function
def load_function(user_class, str_function: str, ptr_default):
	"""
		Load user function

		Parameters:
			- user_class (class): user class
			- str_function (str): field string
			- ptr_default (pointer): default function

		Returns:
			- pointer: user function
	"""
	try:
		# Result
		return getattr(user_class, str_function, ptr_default)

	except Exception as err:
		# Trace
		# print(err)
		# print(traceback.format_exc())
		# Result
		return ptr_default


# Class definition
class DefaultConfig:
	"""
		DefaultConfig class: default application configuration
	"""

	# Run
	@staticmethod
	def run(self): time.sleep(0.1)

	# Get time before next activity
	@staticmethod
	def get_time_before_activity(self): return 3600.0

	# Get version
	@staticmethod
	def get_version(self): return "none"

	# Dummy measurement
	@staticmethod
	def get_data(self): return "user=none"

	# Test process
	@staticmethod
	def test(self): return "user    : none"


# Class definition
class UserConfig:
	"""
		UserConfig class: user application configuration
	"""

	# Create resource
	def __init__(self):
		# Manager
		self.source_code = "none"
		self._class_mission = None
		self._ptr_run = None
		self._ptr_next_activity = None
		self._class_command = None
		self._ptr_version = None
		self._ptr_measurement = None
		self._ptr_test = None

	# Load user configuration
	def load(self):
		"""
			Load user configuration
		"""
		# Read user configuration
		str_source_code = read_configuration("APPLICATION", "source_code")
		str_class_mission = read_configuration("MISSION", "class_mission")
		str_function_run = read_configuration("MISSION", "function_run")
		str_function_time_before_activity = read_configuration("MISSION", "function_time_before_activity")
		str_class_command = read_configuration("COMMAND", "class_command")
		str_function_version = read_configuration("COMMAND", "function_version")
		str_function_measurement = read_configuration("COMMAND", "function_measurement")
		str_function_test = read_configuration("COMMAND", "function_test")
		if not str_source_code == "":
			self.source_code = str_source_code
		# Load mission configuration
		user_class_mission = load_class(str_source_code, str_class_mission, DefaultConfig)
		self._ptr_run = load_function(user_class_mission, str_function_run, default_driver.run)
		self._ptr_next_activity = load_function(user_class_mission, str_function_time_before_activity, default_driver.get_time_before_activity)
		self._class_mission = user_class_mission()
		# Load command configuration
		user_class_command = load_class(str_source_code, str_class_command, DefaultConfig)
		self._ptr_version = load_function(user_class_command, str_function_version, default_driver.get_version)
		self._ptr_measurement = load_function(user_class_command, str_function_measurement, default_driver.get_data)
		self._ptr_test = load_function(user_class_command, str_function_test, default_driver.test)
		self._class_command = user_class_command()

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Call function
		self._ptr_run(self._class_mission)

	# Get time before next activity
	def get_time_before_activity(self) -> float:
		"""
			Get the time remaining before the next activity

			Returns:
				- float: time remaining before the next activity (sec)
		"""
		# Call function
		return self._ptr_next_activity(self._class_mission)

	# Get version
	def get_version(self) -> str:
		"""
			Get version

			Returns:
				- str: version string
		"""
		# Call function
		return self._ptr_version(self._class_command)

	# Dummy measurement
	def get_data(self) -> str:
		"""
			Dummy measurement

			Returns:
				- str: result string (eg: "c1=15.367", "no reply" if error)
		"""
		# Call function
		return self._ptr_measurement(self._class_command)

	# Test process
	def test(self) -> str:
		"""
			Test process

			Returns:
				- str: result string ("xxxxxxxx: ok/error" format)
		"""
		# Call function
		return self._ptr_test(self._class_command)


# Create resources
default_driver = DefaultConfig()
user_driver = UserConfig()
user_driver.load()

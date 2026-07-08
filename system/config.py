#!/bin/python
# -*- coding: utf-8 -*-
"""
	config.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-07-03"
__version__ = "1.0.2"


# Standard libraries
import os
import sys
import time
from configparser import RawConfigParser, NoSectionError, NoOptionError

# Project libraries
from system.trace_lib import trace_log

# Configuration
USER_MAX_NUMBER = 4


# Read user configuration field
def read_configuration(config_file: str, section: str, field: str) -> str:
	"""
		Read user configuration field

		Parameters:
			- config_file (str) : filename
			- section (str): section string
			- field (str): field string

		Returns:
			- str: field value
	"""
	try:
		# Read config
		config = RawConfigParser()
		config.read("./user/"+config_file)
		# Result
		return config.get(section, field)

	except (NoSectionError, NoOptionError, KeyError, ValueError, AttributeError):
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
		# Undefined
		if not source_code or source_code == "undefined":
			return default_class
		# Load module
		sys.path.insert(1, "./user")
		user_module = __import__(source_code.split(".")[0])
		# Result
		return getattr(user_module, class_name, default_class)

	except (ModuleNotFoundError, AttributeError, ImportError):
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

	except TypeError:
		# Result
		return ptr_default


# Class definition
class DefaultConfig:
	"""
		DefaultConfig class: default application configuration
	"""

	# Create resource
	def __init__(self, user_index: int = 0):
		# Manager
		self.user_index = user_index

	# Run
	# noinspection PyMethodMayBeStatic
	def run(self): time.sleep(0.1)

	# Get time before next activity
	# noinspection PyMethodMayBeStatic
	def get_time_before_activity(self): return 3600.0

	# Get version
	# noinspection PyMethodMayBeStatic
	def get_version(self): return "none"

	# Dummy measurement
	# noinspection PyMethodMayBeStatic
	def get_data(self): return "none"

	# Test process
	# noinspection PyMethodMayBeStatic
	def test(self): return "user    : none"


# Class definition
class UserConfig:
	"""
		UserConfig class: user application configuration

		user_index = 0 → user.ini (mono-user legacy mode)
		user_index >=1 → user{i}.ini (multi-user)
	"""

	# Create resource
	def __init__(self, config_file: str, user_index: int = 0):
		# Manager
		self.config_file = config_file
		self.user_index = user_index
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
		str_source_code = read_configuration(self.config_file, "APPLICATION", "source_code")
		str_class_mission = read_configuration(self.config_file, "MISSION", "class_mission")
		str_function_run = read_configuration(self.config_file, "MISSION", "function_run")
		str_function_time_before_activity = read_configuration(self.config_file, "MISSION", "function_time_before_activity")
		str_class_command = read_configuration(self.config_file, "COMMAND", "class_command")
		str_function_version = read_configuration(self.config_file, "COMMAND", "function_version")
		str_function_measurement = read_configuration(self.config_file, "COMMAND", "function_measurement")
		str_function_test = read_configuration(self.config_file, "COMMAND", "function_test")
		if not str_source_code == "":
			self.source_code = str_source_code
		# Load mission configuration
		user_class_mission = load_class(str_source_code, str_class_mission, DefaultConfig)
		self._ptr_run = load_function(user_class_mission, str_function_run, DefaultConfig.run)
		self._ptr_next_activity = load_function(user_class_mission, str_function_time_before_activity, DefaultConfig.get_time_before_activity)
		self._class_mission = user_class_mission(self.user_index)
		# Load command configuration
		user_class_command = load_class(str_source_code, str_class_command, DefaultConfig)
		self._ptr_version = load_function(user_class_command, str_function_version, DefaultConfig.get_version)
		self._ptr_measurement = load_function(user_class_command, str_function_measurement, DefaultConfig.get_data)
		self._ptr_test = load_function(user_class_command, str_function_test, DefaultConfig.test)
		self._class_command = user_class_command(self.user_index)

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
				- str: result string ("id_8_digits: ok/error" format)
		"""
		# Call function
		return self._ptr_test(self._class_command)


# Remove file if exists
def remove_file_if_exists(path: str):
	if os.path.exists(path):
		os.remove(path)


# Create resources
default_driver = DefaultConfig()
user_drivers = []
# Mono-user legacy
if os.path.exists("./user/user.ini"):
	driver = UserConfig("user.ini", 0)
	trace_log(f"CONFIG   > Load {driver.config_file}")
	driver.load()
	user_drivers.append(driver)
	for i in range(1, USER_MAX_NUMBER + 1):
		remove_file_if_exists(f"./share/user{i}.txt")
# Multi-user
else:
	for i in range(1, USER_MAX_NUMBER + 1):
		if not os.path.exists(f"./user/user{i}.ini"):
			continue
		driver = UserConfig(f"user{i}.ini", i)
		trace_log(f"CONFIG   > Load {driver.config_file}")
		driver.load()
		user_drivers.append(driver)
	loaded_count = len(user_drivers)
	remove_file_if_exists("./share/user.txt")
	for i in range(loaded_count + 1, USER_MAX_NUMBER + 1):
		remove_file_if_exists(f"./share/user{i}.txt")

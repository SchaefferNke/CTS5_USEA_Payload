#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	config.py
	"""

# Standard libraries
import sys
import time
from configparser import RawConfigParser


# Class definition
class UserDefault:
	"""
		UserDefault class: default application configuration
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


# Create resources
user_default = UserDefault()


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
		value = config.get(section, field)
		# Result
		return value

	except Exception as err:
		# Result
		return "default"


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
		# Load class
		user_class = getattr(user_module, class_name)
		# Result
		return user_class

	except Exception as err:
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
		# Get attribute
		ptr_function = getattr(user_class, str_function)
		# Result
		return ptr_function

	except Exception as err:
		# Result
		return ptr_default


# Class definition
class UserConfig:
	"""
		UserConfig class: user application configuration
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.class_mission = ""
		self.ptr_run = ""
		self.ptr_next_activity = ""
		self.class_command = ""
		self.ptr_version = ""
		self.ptr_measurement = ""
		self.ptr_test = ""

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
		# Load mission configuration
		user_class_mission = load_class(str_source_code, str_class_mission, user_default)
		self.ptr_run = load_function(user_class_mission, str_function_run, user_default.run)
		self.ptr_next_activity = load_function(user_class_mission, str_function_time_before_activity, user_default.get_time_before_activity)
		self.class_mission = user_class_mission()
		# Load command configuration
		user_class_command = load_class(str_source_code, str_class_command, user_default)
		self.ptr_version = load_function(user_class_command, str_function_version, user_default.get_version)
		self.ptr_measurement = load_function(user_class_command, str_function_measurement, user_default.get_data)
		self.ptr_test = load_function(user_class_command, str_function_test, user_default.test)
		self.class_command = user_class_command()

	# Run task
	def run(self):
		"""
			Working task
			"""
		# Call function
		self.ptr_run(self.class_mission)

	# Get time before next activity
	def get_time_before_activity(self) -> float:
		"""
			Get the time remaining before the next activity

			Returns:
				- float: time remaining before the next activity (sec)
			"""
		# Call function
		return self.ptr_next_activity(self.class_mission)

	# Get version
	def get_version(self) -> str:
		"""
			Get version

			Returns:
				- str: version string
			"""
		# Call function
		return self.ptr_version(self.class_command)

	# Dummy measurement
	def get_data(self) -> str:
		"""
			Dummy measurement

			Returns:
				- str: result string (eg: "c1=15.367", "no reply" if error)
			"""
		# Call function
		return self.ptr_measurement(self.class_command)

	# Test process
	def test(self) -> str:
		"""
			Test process

			Returns:
				- str: result string (eg: "senso   : ok", xxxxxxxx: ok/error format)
			"""
		# Call function
		return self.ptr_test(self.class_command)


# Create resources
user_driver = UserConfig()
user_driver.load()

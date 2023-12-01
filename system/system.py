#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	system.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2023-12-01"
__version__ = "1.0.0"

# Standard libraries
import os
import datetime


# Class definition
class DriverSystem:
	"""
		DriverSystem class: manage system commands
	"""

	# Reboot system
	@staticmethod
	def reboot():
		"""
			Reboot system
		"""
		if not os.name == "nt":
			# Reboot
			os.system("sudo reboot")

	# Suspend system
	@staticmethod
	def suspend():
		"""
			Suspend system
		"""
		if not os.name == "nt":
			# Suspend
			os.system("sudo pm-suspend")

	# Restore system clock
	@staticmethod
	def clock_restore():
		"""
			Restore system clock from hardware RTC
		"""
		if not os.name == "nt":
			# Synchronize system clock to hardware RTC
			os.system("sudo hwclock --hctosys --utc")

	# Synchronize system clock
	@staticmethod
	def clock_synchronize(utc: datetime):
		"""
			Synchronize system clock and hardware RTC to external date/time

			Parameters:
				- utc (datetime): new date/time
		"""
		if not os.name == "nt":
			# Set system clock
			os.system("sudo date -u --set=%s" % utc.strftime("20%y-%m-%dT%H:%M:%S"))
			# Synchronize hardware RTC to system clock
			os.system("sudo hwclock --systohc --utc")

	# Program wakealarm
	@staticmethod
	def program_wakealarm(utc: datetime, delay: str):
		"""
			Program wakealarm

			Parameters:
				- utc (datetime): current date/time
				- delay (str): delay time from now
		"""
		if not os.name == "nt":
			# Program wakeup
			os.system("sudo date " + str(utc) + " -d " + delay + " > /sys/class/rtc/rtc0/wakealarm")

	# Set output on
	@staticmethod
	def output_set_on(name: str):
		"""
			Set the output on

			Parameters:
				- name (str): GPIO name (eg: "gpiochip3 8")
		"""
		if not os.name == "nt":
			# Set output on
			os.system("gpioset " + name + "=1")

	# Set output off
	@staticmethod
	def output_set_off(name: str):
		"""
			Set the output off

			Parameters:
				- name (str): GPIO name (eg: "gpiochip3 8")
		"""
		if not os.name == "nt":
			# Set output off
			os.system("gpioset " + name + "=1")

	# Test input state
	@staticmethod
	def input_is_on(name: str) -> bool:
		"""
			Test the input state

			Parameters:
				- name (str): GPIO name (eg: "gpiochip3 8")

			Returns:
				- bool: True if the input is on
		"""
		if not os.name == "nt":
			# Read input
			result = os.system("gpioget " + name)
		else:
			result = "1"
		# Result
		if result == "1":
			return True
		return False

	# Format GPIO string for system access
	@staticmethod
	def format_gpio_name(name: str) -> str:
		"""
			Translates IO name into system GPIO name

			Parameters:
				- name (str): IO name (eg: "GPIO_3_8")

			Returns:
				- str: GPIO name (eg: "gpiochip3 8")
		"""
		# Format
		split = name.split("_")
		# Result
		return "gpiochip" + str(int(split[1])-1) + " " + split[2]

	# Format serial string for system access
	@staticmethod
	def format_serial_name(name: str) -> str:
		"""
			Translates serial name into system serial name

			Parameters:
				- name (str): serial name (eg: "COM_1")

			Returns:
				- str: system serial name for system access (eg: "/dev/tty0")
		"""
		# Format
		split = name.split("_")
		if not os.name == "nt":
			result = "/dev/tty" + str(int(split[1])-1)
		else:
			result = "COM" + split[1]
		# Result
		return result


# Create resources
system_driver = DriverSystem()

#!/bin/python
# -*- coding: utf-8 -*-
"""
	rtc.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-07-03"
__version__ = "1.0.2"

# Standard libraries
import datetime

# Project libraries
from system.system_lib import system_driver
from system.trace_lib import trace_log


# Class definition
class DriverRTC:
	"""
		DriverRTC class: manage hardware RTC
	"""

	# Restore system clock
	@staticmethod
	def restore():
		"""
			Restore system clock from hardware RTC
		"""
		# Synchronize system clock to hardware RTC
		system_driver.clock_restore()
		# Check date
		if datetime.datetime.now().date().year < 2024:
			# Default date
			now = datetime.datetime.now()
			utc = now.replace(year=2024, month=5, day=29, hour=12, minute=0, second=0, microsecond=0)
			# Set system clock
			system_driver.clock_synchronize(utc)
		# Trace
		trace_log("RTC      > Restore=" + datetime.datetime.now().strftime("20%y-%m-%d %H:%M:%S"))

	# Synchronize system clock
	@staticmethod
	def synchronize(utc: datetime):
		"""
			Synchronize system clock and hardware RTC to external date/time

			Parameters:
				- utc (datetime): new date/time
		"""
		# Synchronize system clock and hardware RTC to external clock
		system_driver.clock_synchronize(utc)
		# Trace
		trace_log("RTC      > Synchronize=" + datetime.datetime.now().strftime("20%y-%m-%d %H:%M:%S"))

	# Program wakealarm in sleep mode (S3)
	@staticmethod
	def program_wakealarm_sleep(delay: int):
		"""
			Program wakealarm (Sleep)

			Parameters:
				- delay (int): delay time from now (seconds)
		"""
		# Trace
		trace_log("RTC      > Awake system in " + str(delay) + " seconds")
		# Program wakeup
		system_driver.program_wakealarm_sleep(delay)
		# Trace
		trace_log("RTC      > Awake")

	# Program wakealarm in sleep mode (S1)
	@staticmethod
	def program_wakealarm_standby(delay: int):
		"""
			Program wakealarm (Standby)

			Parameters:
				- delay (int): delay time from now (seconds)
		"""
		# Trace
		trace_log("RTC      > Awake system in " + str(delay) + " seconds")
		# Program wakeup
		system_driver.program_wakealarm_standby(delay)
		# Trace
		trace_log("RTC      > Awake")


# Create resources
rtc_driver = DriverRTC()

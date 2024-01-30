#!/bin/python
# -*- coding: utf-8 -*-
"""
	rtc.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-01-29"
__version__ = "1.0.0"

# Standard libraries
import datetime

# Project libraries
from system.system import system_driver
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
		# Trace
		trace_log("./", "RTC      > Restore=" + datetime.datetime.now().strftime("20%y-%m-%d %H:%M:%S"))

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
		trace_log("./", "RTC      > Synchronize=" + datetime.datetime.now().strftime("20%y-%m-%d %H:%M:%S"))

	# Program wakealarm
	@staticmethod
	def program_wakealarm(delay: str):
		"""
			Program wakealarm

			Parameters:
				- delay (str): delay time from now (seconds)
		"""
		# Compute awake date
		utc = datetime.datetime.now()
		# Program wakeup
		system_driver.program_wakealarm(delay)
		# Trace
		trace_log("./", "RTC      > wakealarm=" + utc.strftime("20%y-%m-%d %H:%M:%S") + " + " + delay)


# Create resources
rtc_driver = DriverRTC()

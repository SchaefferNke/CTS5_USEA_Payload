#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	rtc.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2023-11-07"
__version__ = "1.0.0"

# Standard libraries
import os
import datetime


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
		if not os.name == "nt":
			# Synchronize system clock to hardware RTC
			os.system("sudo hwclock --hctosys --utc")

	# Synchronize system clock
	@staticmethod
	def synchronize(utc: datetime):
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
	def program_wakealarm(delay: str):
		"""
			Program wakealarm

			Parameters:
				- delay (str): delay time from now
		"""
		# Suspend system
		if not os.name == "nt":
			# Compute awake date
			utc = datetime.datetime.now()
			# Program wakeup
			os.system("sudo date " + str(utc) + " -d " + delay + " > /sys/class/rtc/rtc0/wakealarm")


# Create resources
rtc_driver = DriverRTC()

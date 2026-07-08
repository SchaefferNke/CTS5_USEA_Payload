#!/bin/python
# -*- coding: utf-8 -*-
"""
	system_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-07-03"
__version__ = "1.0.2"

# Standard libraries
import os
import time
import datetime
import subprocess


# Class definition
class DriverSystem:
	"""
		DriverSystem class: manage system commands
	"""

	# Create resource
	def __init__(self):
		# Watchdog
		self._watchdog_cpt = 0

	# Feed watchdog daemon
	def watchdog_feed(self):
		"""
			Refresh watchdog daemon
		"""
		if not os.name == "nt":
			# Refresh watchdog counter
			self._watchdog_cpt += 1
			try:
				with open("/tmp/_watchdog", "w") as file_watchdog:
					file_watchdog.write(str(self._watchdog_cpt))
			except IOError:
				return

	# System boot validation
	@staticmethod
	def boot_ok():
		"""
			Validate system boot
		"""
		if not os.name == "nt":
			# Save
			try:
				subprocess.run(["fw_setenv", "bootcount",         "0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
				subprocess.run(["fw_setenv", "upgrade_available", "0"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
			except subprocess.CalledProcessError:
				return

	# Reboot system
	@staticmethod
	def reboot():
		"""
			Reboot system
		"""
		if not os.name == "nt":
			# Reboot
			os.system("sudo reboot")

	# Restore system clock
	@staticmethod
	def clock_restore():
		"""
			Restore system clock from hardware RTC
		"""
		if not os.name == "nt":
			# Synchronize system clock to hardware RTC
			os.system("sudo hwclock -s")

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
			os.system("sudo date -s '%s'" % utc.strftime("20%y-%m-%d %H:%M:%S"))
			# Synchronize hardware RTC to system clock
			os.system("sudo hwclock -w")

	# Program wakealarm in sleep mode (S3)
	@staticmethod
	def program_wakealarm_sleep(delay: int):
		"""
			Program wakealarm (Suspend-to-RAM)

			Parameters:
				- delay (int): delay time from now (seconds)
		"""
		if not os.name == "nt":
			# Flush files buffering
			os.system("sudo sync")
			# Wait
			time.sleep(0.25)
			# Program wakeup
			os.system("sudo rtcwake -d /dev/rtc0 -m mem -s " + str(delay))
		else:
			# Wait
			time.sleep(delay)

	# Program wakealarm in standby mode (S1)
	@staticmethod
	def program_wakealarm_standby(delay: int):
		"""
			Program wakealarm (Standby)

			Parameters:
				- delay (int): delay time from now (seconds)
		"""
		if not os.name == "nt":
			# Flush files buffering
			os.system("sudo sync")
			# Wait
			time.sleep(0.25)
			# Program wakeup
			os.system("sudo rtcwake -d /dev/rtc0 -m standby -s " + str(delay))
		else:
			# Wait
			time.sleep(delay)

	# Get Disk1 path
	@staticmethod
	def disk1_path() -> str:
		"""
			Disk1 path

			Returns:
				- str: Application path
		"""
		if not os.name == "nt":
			result = "/opt/app"
		else:
			result = "/"
		# Result
		return result

	# Get Disk2 path
	@staticmethod
	def disk2_path() -> str:
		"""
			Disk2 path

			Returns:
				- str: Data path
		"""
		if not os.name == "nt":
			result = "/media/sd"
		else:
			result = "/"
		# Result
		return result

	# Get Disk2 status
	@staticmethod
	def disk2_is_present() -> bool:
		"""
			Disk2 detection

			Returns:
				- bool: True if the SD card is inserted
		"""
		if not os.name == "nt":
			# Detect SD card
			result = os.system("sudo ls /dev/mmcblk0 >/dev/null 2>&1")
		else:
			result = 256
		# Result
		if result == 0:
			return True
		return False

	# Format Disk2
	@staticmethod
	def disk2_format() -> bool:
		"""
			Disk2 formatting

			Returns:
				- bool: True if the SD card is formatted
		"""
		if os.name == "nt":
			return False
		# Define partition and mount point
		partition = "/dev/mmcblk0p1"
		mount_point = "/media/sd"
		# Check if partition exists
		if not os.path.exists(partition):
			return False
		# Ensure the mount point exists
		os.makedirs(mount_point, exist_ok=True)
		# Unmount if already mounted
		os.system(f"sudo umount {partition} 2>/dev/null || true")
		time.sleep(1.0)
		# Format SD card with FAT32 (silently) and sync
		if os.system(f"sudo LC_ALL=C sh -c 'mkfs.vfat -F 32 {partition} >/dev/null 2>&1 && sync'") != 0:
			return False
		# Mount the SD card
		os.system(f"sudo mount {partition} {mount_point} 2>/dev/null")
		time.sleep(1.0)
		# Return True, assuming reboot will be done to finalize
		return True

	# Test Disk2
	@staticmethod
	def disk2_test() -> bool:
		"""
			Disk2 test

			Returns:
				- bool: True if the SD card test succeed
		"""
		if os.name == "nt":
			return False
		# Check mount
		if not os.path.ismount("/media/sd"):
			return False
		# Write test file
		try:
			with open("/media/sd/test.txt", "w") as f:
				f.write("success")
			os.system("sync")
		except OSError:
			return False
		# Result
		return True

	# Set output on
	@staticmethod
	def output_set_on(name: str):
		"""
			Set the output on

			Parameters:
				- name (str): GPIO name (eg: "gpiochip2 8")
		"""
		if not os.name == "nt":
			# Set output on
			os.system("sudo gpioset " + name + "=1")

	# Set output off
	@staticmethod
	def output_set_off(name: str):
		"""
			Set the output off

			Parameters:
				- name (str): GPIO name (eg: "gpiochip2 8")
		"""
		if not os.name == "nt":
			# Set output off
			os.system("sudo gpioset " + name + "=0")

	# Get input state
	@staticmethod
	def input_get(name: str) -> bool:
		"""
			Get the input state

			Parameters:
				- name (str): GPIO name (eg: "gpiochip2 8")

			Returns:
				- bool: True if the input is on
		"""
		if not os.name == "nt":
			# Read input
			cmd = "sudo gpioget " + name
			cmd_result = subprocess.run(cmd.split(), capture_output=True)
			split = cmd_result.stdout.decode().split()
			result = split[0]
		else:
			result = "1"
		# Result
		if result == "0":
			return False
		return True

	# Format GPIO string for system access
	@staticmethod
	def format_gpio_name(name: str) -> str:
		"""
			Translates IO name into system GPIO name

			Parameters:
				- name (str): IO name (eg: "GPIO_3_8")

			Returns:
				- str: GPIO name (eg: "gpiochip2 8")
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
				- str: system serial name for system access (eg: "/dev/ttymxc0")
		"""
		# Format
		split = name.split("_")
		if not os.name == "nt":
			# Format
			result = "/dev/ttymxc" + str(int(split[1])-1)
		else:
			result = "COM" + split[1]
		# Result
		return result


# Create resources
system_driver = DriverSystem()

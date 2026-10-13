#!/bin/python
# -*- coding: utf-8 -*-
"""
	technical.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-09-30"
__version__ = "1.0.3"

# Standard libraries
import os
import sys
import datetime
import time
import traceback

# Third-party libraries
import psutil

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.system_lib import system_driver
from system.timer_lib import DriverTimer
from system.share_lib import DataShare, FileShare, get_navigation, get_profile
from system.trace_lib import trace_log
from system.const import *


# Class definition
class DriverTechnicalSystem:
	"""
		DriverTechnicalSystem class: system monitoring
	"""

	# Create resource
	def __init__(self):
		# Manager
		self._step = USEA_TECHNICAL_STEP_IDLE
		self._timer = DriverTimer("technical")
		self._boot_count = FileShare("boot.txt")
		self._share_step = DataShare("tech_step")
		# config.py include makes circular dependency
		from system.config import user_drivers
		# User access
		self._user_step = []
		self._payloads = []
		for driver in user_drivers:
			if driver.user_index == 0:
				self._user_step.append(DataShare("user_step"))
			else:
				self._user_step.append(DataShare(f"user{driver.user_index}_step"))
			self._payloads.append(driver)
		# Initialize CPU usage
		psutil.cpu_percent(interval=None)
		# Counters
		self._activity_run = 0
		self._cpu_freq = 0.0
		self._cpu_freq_max = 0.0
		self._cpu_freq_sum = 0.0
		self._cpu_usage = 0.0
		self._cpu_usage_max = 0.0
		self._cpu_usage_sum = 0.0
		self._cpu_temp = 0.0
		self._cpu_temp_max = 0.0
		self._cpu_temp_sum = 0.0
		self._mem_usage = 0.0
		self._mem_usage_max = 0.0
		self._mem_usage_sum = 0.0
		self._disk1_usage = 0.0
		self._disk2_usage = 0.0
		# Check SD card
		self._disk2_is_present = False
		# Power-on alarm
		self._power_on = True

	# Reset diagnosis counters
	def diagnosis_reset(self):
		"""
			Reset the diagnosis counters
		"""
		# Reset
		self._activity_run = 0
		self._cpu_freq_max = 0.0
		self._cpu_freq_sum = 0.0
		self._cpu_usage_max = 0.0
		self._cpu_usage_sum = 0.0
		self._cpu_temp_max = 0.0
		self._cpu_temp_sum = 0.0
		self._mem_usage_max = 0.0
		self._mem_usage_sum = 0.0

	# CPU frequency
	@staticmethod
	def _read_cpu_freq() -> float:
		try:
			freq = psutil.cpu_freq()
			return float(freq.current) if freq and freq.current is not None else 0.0
		except (psutil.AccessDenied, psutil.Error, OSError, TypeError, ValueError):
			return 0.0

	# CPU usage
	@staticmethod
	def _read_cpu_usage() -> float:
		try:
			usage = psutil.cpu_percent(interval=None)
			return float(usage) if usage is not None else 0.0
		except (psutil.AccessDenied, psutil.Error, OSError, TypeError, ValueError):
			return 0.0

	# CPU temperature
	@staticmethod
	def _read_cpu_temperature() -> float:
		if os.name == "nt":
			return 0.0
		try:
			temps = psutil.sensors_temperatures(fahrenheit=False)
		except (TypeError, AttributeError, KeyError, OSError, psutil.Error, RuntimeError):
			trace_log("TECH     > psutil sensors_temperatures failure")
			return 0.0
		if not isinstance(temps, dict):
			return 0.0
		for entries in temps.values():
			if not entries:
				continue
			for entry in entries:
				current = getattr(entry, "current", None)
				if isinstance(current, (int, float)):
					return float(current)
		return 0.0

	# Memory usage
	@staticmethod
	def _read_memory_usage() -> float:
		try:
			mem = psutil.virtual_memory().percent
			return float(mem) if mem is not None else 0.0
		except (psutil.AccessDenied, psutil.Error, OSError, TypeError, ValueError):
			return 0.0

	# Disk usage
	@staticmethod
	def _read_disk_usage() -> tuple[float, float, bool]:
		try:
			path1 = system_driver.disk1_path()
			if os.path.exists(path1):
				disk1_usage = float(psutil.disk_usage(path1).percent)
			else:
				disk1_usage = 0.0
		except (OSError, PermissionError, AttributeError):
			disk1_usage = 0.0
		disk2_usage = 0.0
		try:
			disk2_present = bool(system_driver.disk2_is_present())
		except (OSError, AttributeError):
			disk2_present = False
		if disk2_present:
			try:
				path2 = system_driver.disk2_path()
				if os.path.exists(path2):
					disk2_usage = float(psutil.disk_usage(path2).percent)
			except (OSError, PermissionError, AttributeError):
				disk2_usage = 0.0
		return disk1_usage, disk2_usage, disk2_present

	# Read metrics
	def _read_all_metrics(self):
		# EMA filters
		alpha_cpu_usage = 0.5
		alpha_cpu_freq = 0.3
		new_cpu_usage = self._read_cpu_usage()
		new_cpu_freq = self._read_cpu_freq()
		if self._activity_run == 0:
			self._cpu_usage = new_cpu_usage
			self._cpu_freq = new_cpu_freq
		else:
			self._cpu_usage = alpha_cpu_usage * new_cpu_usage + (1 - alpha_cpu_usage) * self._cpu_usage
			self._cpu_freq = alpha_cpu_freq * new_cpu_freq + (1 - alpha_cpu_freq) * self._cpu_freq
		self._cpu_temp = self._read_cpu_temperature()
		self._mem_usage = self._read_memory_usage()
		self._disk1_usage, self._disk2_usage, self._disk2_is_present = self._read_disk_usage()

	# Make a diagnosis
	def diagnosis_run(self):
		"""
			Make an instantaneous diagnosis
		"""
		try:
			# System activity
			self._activity_run += 1
			# Read metrics
			self._read_all_metrics()
			# CPU frequency
			self._cpu_freq_sum += self._cpu_freq
			self._cpu_freq_max = max(self._cpu_freq_max, self._cpu_freq)
			# CPU usage
			self._cpu_usage_sum += self._cpu_usage
			self._cpu_usage_max = max(self._cpu_usage_max, self._cpu_usage)
			# CPU temperature
			self._cpu_temp_sum += self._cpu_temp
			self._cpu_temp_max = max(self._cpu_temp_max, self._cpu_temp)
			# Memory usage
			self._mem_usage_sum += self._mem_usage
			self._mem_usage_max = max(self._mem_usage_max, self._mem_usage)
		except (TypeError, ValueError, AttributeError):
			pass

	# Status json
	def status_json(self) -> object:
		"""
			Save json information

			Returns:
				- object: json object
		"""
		# CPU frequency rounded
		cpu_freq = round(self._cpu_freq / 5) * 5
		# Disk status
		try:
			disk1_size = psutil.disk_usage(system_driver.disk1_path()).total / (1024.0 ** 3)
		except (psutil.Error, OSError):
			disk1_size = 0.0
		disk2_size = 0.0
		if self._disk2_is_present:
			try:
				disk2_size = psutil.disk_usage(system_driver.disk2_path()).total / (1024.0 ** 3)
			except (psutil.Error, OSError):
				disk2_size = 0.0
		# User drivers identification
		versions = [payload.get_version() for payload in self._payloads]
		# Save
		result = {
			"board-name": "USEA-Payload",
			"software-version": USEA_VERSION + "-" + "/".join(versions),
			"system-time": datetime.datetime.now().strftime("20%y-%m-%d %H:%M:%S"),
			"cpu-speed": f"{cpu_freq:.0f}",
			"cpu-usage": f"{self._cpu_usage:.1f}",
			"cpu-temperature": f"{self._cpu_temp:.1f}",
			"memory-usage": f"{self._mem_usage:.1f}",
			"disk1-size": f"{disk1_size:.1f}",
			"disk1-usage": f"{self._disk1_usage:.1f}",
			"disk2-present": str(self._disk2_is_present),
			"disk2-size": f"{disk2_size:.1f}",
			"disk2-usage": f"{self._disk2_usage:.1f}"}
		# Result
		return result

	# Save diagnosis
	def diagnosis_save(self):
		"""
			Save diagnosis into technical file
		"""
		# Compute average safely
		def safe_average(sum_value, count):
			return sum_value / count if count > 0 else 0.0
		# System activity
		activity_run = self._activity_run / 60.0
		# CPU frequency
		cpu_freq = safe_average(self._cpu_freq_sum, self._activity_run)
		# CPU usage
		cpu_usage = safe_average(self._cpu_usage_sum, self._activity_run)
		# CPU temperature
		cpu_temp = safe_average(self._cpu_temp_sum, self._activity_run)
		# Memory usage
		mem_usage = safe_average(self._mem_usage_sum, self._activity_run)
		# Boot counter
		self._boot_count.read()
		# Create names
		dest_file = "payload/" + get_profile() + "_payload.txt"
		user_file = "share/technical.txt"
		# Open file
		with open(dest_file, "w", encoding="utf-8", newline="\r\n") as tech_file:
			# Write system info
			if self._disk2_is_present:
				tech_file.write(
					"[PAYLOAD]\n" +
					"CPU speed=" + f"{cpu_freq:.0f}" + "/" + f"{self._cpu_freq_max:.0f}" + " MHz\n" +
					"CPU usage=" + f"{cpu_usage:.0f}" + "/" + f"{self._cpu_usage_max:.0f}" + " %\n" +
					"CPU temperature=" + f"{cpu_temp:.1f}" + "/" + f"{self._cpu_temp_max:.1f}" + " degC\n" +
					"Memory usage=" + f"{mem_usage:.0f}" + "/" + f"{self._mem_usage_max:.0f}" + " %\n" +
					"Disk_1 usage=" + f"{self._disk1_usage:.1f}" + " %\n" +
					"Disk_2 usage=" + f"{self._disk2_usage:.1f}" + " %\n" +
					"Boot count=" + self._boot_count.content.string + "\n")
			else:
				tech_file.write(
					"[PAYLOAD]\n" +
					"CPU speed=" + f"{cpu_freq:.0f}" + "/" + f"{self._cpu_freq_max:.0f}" + " MHz\n" +
					"CPU usage=" + f"{cpu_usage:.0f}" + "/" + f"{self._cpu_usage_max:.0f}" + " %\n" +
					"CPU temperature=" + f"{cpu_temp:.1f}" + "/" + f"{self._cpu_temp_max:.1f}" + " degC\n" +
					"Memory usage=" + f"{mem_usage:.0f}" + "/" + f"{self._mem_usage_max:.0f}" + " %\n" +
					"Disk_1 usage=" + f"{self._disk1_usage:.1f}" + " %\n" +
					"Boot count=" + self._boot_count.content.string + "\n")
			# Write power info
			tech_file.write(
				"[POWER]\n" +
				"Payload=" + f"{activity_run:.0f}" + " min\n")
			# Write user info
			if os.path.exists(user_file):
				# Read user info
				with open(user_file, "r") as src_file:
					content = src_file.read()
				# Write user info
				tech_file.write(content)
				# Remove user file
				os.remove(user_file)
			else:
				# Write alarm
				if self._power_on:
					# Clear flag
					self._power_on = False
					# Write alarm info
					tech_file.write(
						"[ALARM]\n" +
						"Power-on (PAYLOAD)\n")

	# Save metadata
	def metadata_save(self):
		"""
			Save metadata into technical file
		"""
		# Create names
		dest_file = "payload/payload.xml"
		# User drivers identification
		versions = [payload.get_version() for payload in self._payloads]
		drivers = [payload.source_code for payload in self._payloads]
		# Open file
		with open(dest_file, "w", encoding="utf-8", newline="\r\n") as metadata_file:
			# Write system info
			if system_driver.disk2_is_present():
				metadata_file.write(
					"\t\t<MEASURE_BOARD " +
					"Model=\"PAYLOAD\" " +
					"Firmware=\"" + USEA_VERSION + "-" + "/".join(versions) + "\" " +
					"Driver=\"" + "/".join(drivers) + "\" " +
					"SDCard=\"Installed\"" +
					"/>\n")
			else:
				metadata_file.write(
					"\t\t<MEASURE_BOARD " +
					"Model=\"PAYLOAD\" " +
					"Firmware=\"" + USEA_VERSION + "-" + "/".join(versions) + "\" " +
					"Driver=\"" + "/".join(drivers) + "\" " +
					"SDCard=\"Not installed\"" +
					"/>\n")

	# Read boot count
	def boot_count(self) -> str:
		"""
			Read boot count

			Returns:
				- str: boot count value
		"""
		# Result
		return self._boot_count.content.string

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Scheduler
		manager(self)


# Class definition
class DriverTechnicalUser:
	"""
		DriverTechnicalUser class: user monitoring

		Parameters:
			- name (str): user identification string (eg: "SENSO")
	"""

	# Create resource
	def __init__(self, name):
		# Manager
		self._name = name
		# Failure flags
		self._error_count = 0
		self._alarm_count = 0
		self._successive_failure_count = 0
		self._is_broken = False

	# Reset diagnosis
	def diagnosis_reset(self):
		"""
			Reset the diagnosis counters and flags
		"""
		# Reset
		self._error_count = 0
		self._alarm_count = 0
		self._successive_failure_count = 0
		self._is_broken = False

	# Update success diagnosis
	def diagnosis_count_success(self):
		"""
			Increment success counter
		"""
		# Reset counter
		self._successive_failure_count = 0

	# Update error diagnosis
	def diagnosis_count_error(self):
		"""
			Increment error counter
		"""
		# Increment
		self._error_count += 1
		self._successive_failure_count += 1

	# Update alarm diagnosis
	def diagnosis_count_alarm(self):
		"""
			Increment alarm counter
		"""
		# Increment
		self._alarm_count += 1

	# Update broken diagnosis
	def diagnosis_count_broken(self):
		"""
			Set broken flag
		"""
		# Set flag
		self._is_broken = True

	# Get successive errors number
	def diagnosis_get_successive_failure(self) -> int:
		"""
			Get successive errors counter

			Returns:
				- int: number of successive errors
		"""
		# Result
		return self._successive_failure_count

	# Get broken diagnosis
	def diagnosis_is_broken(self) -> bool:
		"""
			Get broken status

			Returns:
				- bool: True if sensor flag is set
		"""
		# Result
		return self._is_broken

	# Save diagnosis
	def diagnosis_save(self):
		"""
			Save diagnosis into technical file
		"""
		# If errors
		if self._error_count or self._alarm_count or self._is_broken:
			# Create name
			error_dst_name = "share/technical.txt"
			# Write content
			with open(error_dst_name, "w", encoding="utf-8", newline="\r\n") as file_dst:
				file_dst.write("[ALARM]\n")
				if self._is_broken:
					file_dst.write(self._name + " broken\n")
				else:
					if self._error_count:
						file_dst.write(self._name + " default (" + str(self._error_count) + ")\n")
				if self._alarm_count:
					file_dst.write(self._name + " alarm (" + str(self._alarm_count) + ")\n")


# Create resources
technical_driver = DriverTechnicalSystem()


# Manager
def manager(self):
	"""
		Running task
	"""

	# Trace
	trace_log("TECH     > Activate")

	# Read boot counter
	self._boot_count.read()
	# Counter is empty?
	if self._boot_count.content.string == "?":
		# Initialize boot counter
		self._boot_count.write("1")
	else:
		# Increment boot counter
		self._boot_count.write(str(int(self._boot_count.content.string) + 1))

	# Start timer
	self._timer.start_base_time(1.0)
	# Share step
	self._share_step.write(self._step)

	# Create metadata file
	self.metadata_save()

	# Loop
	while True:
		try:

			# Read resource
			navigation = get_navigation()

			# Wait
			if self._step == USEA_TECHNICAL_STEP_IDLE:
				# Initiating navigation?
				if (
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_DECREASE) or
					(navigation == USEA_NAVIGATION_STATE_DESCENT)):
					# Trace
					trace_log("TECH     > Start monitoring")
					# Reset counters
					self.diagnosis_reset()
					# Start recording
					self._step = USEA_TECHNICAL_STEP_MONITOR
					# Share step
					self._share_step.write(self._step)
				# Wait
				else:
					time.sleep(0.1)

			# Monitoring in progress
			elif self._step == USEA_TECHNICAL_STEP_MONITOR:
				# Navigation still in progress?
				if navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Trace
					trace_log("TECH     > Stop monitoring")
					# Stop treatment
					self._step = USEA_TECHNICAL_STEP_TREAT
					# Share step
					self._share_step.write(self._step)
					# Wait for user process to catch the signal
					time.sleep(0.1)
				# Wait
				else:
					time.sleep(0.1)

			# User treatment
			elif self._step == USEA_TECHNICAL_STEP_TREAT:
				# Treatment in progress?
				all_idle = True
				for i, payload in enumerate(self._payloads):
					step = self._user_step[i]
					if (payload.source_code != "none") and (step.read() != USEA_USER_STEP_IDLE):
						all_idle = False
						break
				# Treatment finished
				if all_idle:
					# Trace
					trace_log("TECH     > Processing")
					# Save diagnosis
					self.diagnosis_save()
					# Stop treatment
					self._step = USEA_TECHNICAL_STEP_IDLE
					# Share step
					self._share_step.write(self._step)
				# Wait
				else:
					time.sleep(0.1)

			# Wait
			else:
				time.sleep(0.1)

			# Monitoring rate
			if self._timer.is_tick():
				# Diagnosis
				self.diagnosis_run()

		# Error
		except Exception as err:
			# Trace
			print(err)
			print(traceback.format_exc())
			# Trace
			trace_log("TECH     > [ERROR]")


# Test function
if __name__ == "__main__":
	# Run
	technical_driver.run()

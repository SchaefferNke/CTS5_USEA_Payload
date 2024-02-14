#!/bin/python
# -*- coding: utf-8 -*-
"""
	technical.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-02-14"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import datetime
import time
import psutil
import traceback

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.system_lib import system_driver
from system.timer_lib import DriverTimer
from system.share_lib import FileShare, DataShare, get_navigation, get_profile
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
		self._step = USEA_PAYLOAD_STEP_IDLE
		self._timer = DriverTimer("technical")
		self._payload_step = DataShare("payload_step")
		self._boot_count = FileShare("boot.txt")
		# config.py include makes circular dependency
		from system.config import user_driver
		self._payload = user_driver
		# Counters
		self._activity_run = 0.0
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

	# Reset diagnosis counters
	def diagnosis_reset(self):
		"""
			Reset the diagnosis counters
		"""
		# Reset
		self._activity_run = 0.0
		self._cpu_freq_max = 0.0
		self._cpu_freq_sum = 0.0
		self._cpu_usage_max = 0.0
		self._cpu_usage_sum = 0.0
		self._cpu_temp_max = 0.0
		self._cpu_temp_sum = 0.0
		self._mem_usage_max = 0.0
		self._mem_usage_sum = 0.0

	# Make a diagnosis
	def diagnosis_run(self):
		"""
			Make an instantaneous diagnosis
		"""
		# System activity
		self._activity_run += 1
		# CPU frequency
		self._cpu_freq = psutil.cpu_freq().current
		self._cpu_freq_sum += self._cpu_freq
		if self._cpu_freq > self._cpu_freq_max:
			self._cpu_freq_max = self._cpu_freq
		# CPU usage
		self._cpu_usage = psutil.cpu_percent(interval=None)
		self._cpu_usage_sum += self._cpu_usage
		if self._cpu_usage > self._cpu_usage_max:
			self._cpu_usage_max = self._cpu_usage
		# CPU temperature
		if not os.name == "nt":
			temps = psutil.sensors_temperatures(fahrenheit=False)
			if "coretemp" in temps:
				self._cpu_temp = temps["coretemp"][0].current
			elif "imx_thermal_zone" in temps:
				self._cpu_temp = temps["imx_thermal_zone"][0].current
		else:
			self._cpu_temp = 0.0
		self._cpu_temp_sum += self._cpu_temp
		if self._cpu_temp > self._cpu_temp_max:
			self._cpu_temp_max = self._cpu_temp
		# Memory usage
		self._mem_usage = psutil.virtual_memory().percent
		self._mem_usage_sum += self._mem_usage
		if self._mem_usage > self._mem_usage_max:
			self._mem_usage_max = self._mem_usage
		# Disk usage
		self._disk1_usage = psutil.disk_usage(system_driver.disk1_path()).percent
		# SD card usage
		self._disk2_usage = 0.0
		self._disk2_is_present = system_driver.disk2_is_present()
		if self._disk2_is_present:
			self._disk2_usage = psutil.disk_usage(system_driver.disk2_path()).percent

	# Status json
	def status_json(self) -> object:
		"""
			Save json information

			Returns:
				- object: json object
		"""
		# CPU frequency
		self._cpu_freq = psutil.cpu_freq().current
		# CPU usage
		self._cpu_usage = psutil.cpu_percent(interval=1)
		# CPU temperature
		if not os.name == "nt":
			temps = psutil.sensors_temperatures(fahrenheit=False)
			if "coretemp" in temps:
				self._cpu_temp = temps["coretemp"][0].current
			elif "imx_thermal_zone" in temps:
				self._cpu_temp = temps["imx_thermal_zone"][0].current
		else:
			self._cpu_temp = 0.0
		# Memory usage
		self._mem_usage = psutil.virtual_memory().percent
		# Disk usage
		disk1_size = psutil.disk_usage(system_driver.disk1_path()).total / (1024.0**3)
		self._disk1_usage = psutil.disk_usage(system_driver.disk1_path()).percent
		# SD card usage
		disk2_size = 0.0
		self._disk2_usage = 0.0
		self._disk2_is_present = system_driver.disk2_is_present()
		if self._disk2_is_present:
			disk2_size = psutil.disk_usage(system_driver.disk2_path()).total / (1024.0**3)
			self._disk2_usage = psutil.disk_usage(system_driver.disk2_path()).percent
		# Save
		result = {
			"board-name": "USEA-Payload",
			"software-version": USEA_VERSION + "-" + self._payload.get_version(),
			"system-time": datetime.datetime.now().strftime("20%y-%m-%d %H:%M:%S"),
			"cpu-speed": f"{self._cpu_freq:.0f}",
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
		# System activity
		activity_run = self._activity_run / 60.0
		# CPU frequency
		cpu_freq = self._cpu_freq_sum / self._activity_run
		# CPU usage
		cpu_usage = self._cpu_usage_sum / self._activity_run
		# CPU temperature
		cpu_temp = self._cpu_temp_sum / self._activity_run
		# Memory usage
		mem_usage = self._mem_usage_sum / self._activity_run
		# Boot counter
		self._boot_count.read()
		# Create names
		dest_file = "payload/" + get_profile() + "_payload.txt"
		user_file = "share/technical.txt"
		# Remove dst file
		if os.path.isfile(dest_file):
			os.remove(dest_file)
		# Open file
		tech_file = open(dest_file, "w")
		# Write system info
		if self._disk2_is_present:
			tech_file.write(
				"[PAYLOAD]\n" +
				"CPU speed=" + f"{cpu_freq:.0f}" + "/" + f"{self._cpu_freq_max:.0f}" + " MHz\n" +
				"CPU usage=" + f"{cpu_usage:.0f}" + "/" + f"{self._cpu_usage_max:.0f}" + " %\n" +
				"CPU temperature=" + f"{cpu_temp:.1f}" + "/" + f"{self._cpu_temp_max:.1f}" + " degC\n" +
				"Memory usage=" + f"{mem_usage:.0f}" + "/" + f"{self._mem_usage_max:.0f}" + " %\n" +
				"Disk_1 usage=" + f"{self._disk1_usage:.0f}" + " %\n" +
				"Disk_2 usage=" + f"{self._disk2_usage:.1f}" + " %\n" +
				"Boot count=" + self._boot_count.content.string + "\n")
		else:
			tech_file.write(
				"[PAYLOAD]\n" +
				"CPU speed=" + f"{cpu_freq:.0f}" + "/" + f"{self._cpu_freq_max:.0f}" + " MHz\n" +
				"CPU usage=" + f"{cpu_usage:.0f}" + "/" + f"{self._cpu_usage_max:.0f}" + " %\n" +
				"CPU temperature=" + f"{cpu_temp:.1f}" + "/" + f"{self._cpu_temp_max:.1f}" + " degC\n" +
				"Memory usage=" + f"{mem_usage:.0f}" + "/" + f"{self._mem_usage_max:.0f}" + " %\n" +
				"Disk_1 usage=" + f"{self._disk1_usage:.0f}" + " %\n" +
				"Boot count=" + self._boot_count.content.string + "\n")
		# Write power info
		tech_file.write(
			"[POWER]\n" +
			"Payload=" + f"{activity_run:.0f}" + " min\n")
		# Write user info
		if os.path.isfile(user_file):
			# Read user info
			src_file = open(user_file, "r")
			content = src_file.read()
			src_file.close()
			# Write user info
			tech_file.write(content)
			# Remove user file
			os.remove(user_file)
		# Close file
		tech_file.close()
		# Clear boot counter
		self._boot_count.write("?")

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
			# Remove dst file
			if os.path.isfile(error_dst_name):
				os.remove(error_dst_name)
			# Write content
			file_dst = open(error_dst_name, "w")
			file_dst.write("[ALARM]\n")
			if self._is_broken:
				file_dst.write(self._name + " broken\n")
			else:
				if self._error_count:
					file_dst.write(self._name + " default (" + str(self._error_count) + ")\n")
			if self._alarm_count:
				file_dst.write(self._name + " alarm (" + str(self._alarm_count) + ")\n")
			file_dst.close()


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

	# Loop
	try:
		while True:

			# Read resource
			navigation = get_navigation()

			# Wait
			if self._step == USEA_PAYLOAD_STEP_IDLE:
				# Initiating descent
				if (
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_DECREASE) or
					(navigation == USEA_NAVIGATION_STATE_DESCENT)):
					# Trace
					trace_log("TECH     > Start monitoring")
					# Reset counters
					self.diagnosis_reset()
					# Start recording
					self._step = USEA_PAYLOAD_STEP_RECORD

			# Navigation
			elif self._step == USEA_PAYLOAD_STEP_RECORD:
				# Navigation in progress
				if navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Start treatment
					self._step = USEA_PAYLOAD_STEP_TREAT

			# Treatment
			elif self._step == USEA_PAYLOAD_STEP_TREAT:
				# Sensor processing
				if not self._payload_step.read() == USEA_PAYLOAD_STEP_TREAT:
					# Trace
					trace_log("TECH     > Stop monitoring")
					# Save diagnosis
					self.diagnosis_save()
					# Stop treatment
					self._step = USEA_PAYLOAD_STEP_IDLE

			# Wait
			else:
				time.sleep(0.1)

			# Monitoring rate
			if self._timer.is_tick():
				# Diagnosis
				self.diagnosis_run()
			# Wait
			else:
				time.sleep(0.1)

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

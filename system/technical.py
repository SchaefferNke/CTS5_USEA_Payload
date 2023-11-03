#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	technical.py
"""

# Standard libraries
import os
import sys
import time
import datetime
import psutil
import traceback

# Project libraries
from system.timer_lib import DriverTimer
from system.share_lib import DataShare, get_navigation, get_profile
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
		self.step = USEA_PAYLOAD_STEP_IDLE
		self.timer = DriverTimer(path, "technical")
		self.payload_step = DataShare("payload_step")
		# Counters
		self.activity_start = 0.0
		self.activity_run = 0.0
		self.cpu_freq_max = 0.0
		self.cpu_freq_sum = 0.0
		self.cpu_usage_max = 0.0
		self.cpu_usage_sum = 0.0
		self.cpu_temp_max = 0.0
		self.cpu_temp_sum = 0.0
		self.mem_usage_max = 0.0
		self.mem_usage_sum = 0.0
		# Check SD card
		# TODO: stratégie détection carte mémoire (démarrage, permanent, ... ?)
		print(psutil.disk_partitions(all=False))
		self.sd_card = False

	# Reset diagnosis counters
	def diagnosis_reset(self):
		"""
			Reset the diagnosis counters
		"""
		# Reset
		self.activity_start = datetime.datetime.now().timestamp()
		self.activity_run = 0.0
		self.cpu_freq_max = 0.0
		self.cpu_freq_sum = 0.0
		self.cpu_usage_max = 0.0
		self.cpu_usage_sum = 0.0
		self.cpu_temp_max = 0.0
		self.cpu_temp_sum = 0.0
		self.mem_usage_max = 0.0
		self.mem_usage_sum = 0.0

	# Make a diagnosis
	def diagnosis_run(self):
		"""
			Make an instantaneous diagnosis
		"""
		# System activity
		self.activity_run += 1.0
		# CPU frequency
		cpu_freq = psutil.cpu_freq().current
		self.cpu_freq_sum = self.cpu_freq_sum + cpu_freq
		if cpu_freq > self.cpu_freq_max:
			self.cpu_freq_max = cpu_freq
		# CPU usage
		cpu_usage = psutil.cpu_percent(interval=None)
		self.cpu_usage_sum = self.cpu_usage_sum + cpu_usage
		if cpu_usage > self.cpu_usage_max:
			self.cpu_usage_max = cpu_usage
		# CPU temperature
		if not os.name == "nt":
			cpu_temp = psutil.sensors_temperatures(fahrenheit=False)
		else:
			cpu_temp = 15.3
		self.cpu_temp_sum = self.cpu_temp_sum + cpu_temp
		if cpu_temp > self.cpu_temp_max:
			self.cpu_temp_max = cpu_temp
		# Memory usage
		mem_usage = 100.0 * psutil.virtual_memory().used / psutil.virtual_memory().total
		self.mem_usage_sum = self.mem_usage_sum + mem_usage
		if mem_usage > self.mem_usage_max:
			self.mem_usage_max = mem_usage

	# Save diagnosis
	def diagnosis_save(self):
		"""
			Save diagnosis into technical file
		"""
		# System activity
		activity_duration = datetime.datetime.now().timestamp() - self.activity_start
		activity_percent = 100.0 * self.activity_run / activity_duration
		if activity_percent > 100.0:
			activity_percent = 100.0
		# CPU frequency
		cpu_freq = self.cpu_freq_sum / self.activity_run
		# CPU usage
		cpu_usage = self.cpu_usage_sum / self.activity_run
		# CPU temperature
		cpu_temp = self.cpu_temp_sum / self.activity_run
		# Memory usage
		mem_usage = self.mem_usage_sum / self.activity_run
		# Disk free
		disk_free = 0.0
		if self.sd_card:
			if not os.name == "nt":
				disk_free = (psutil.disk_usage("/dev/sda1").total - psutil.disk_usage("/dev/sda1").used) / 1073741824.0
		# Create names
		dest_file = path + "payload/" + get_profile(path) + "_payload.txt"
		user_file = path + "share/technical.txt"
		# Remove dst file
		if os.path.isfile(dest_file):
			os.remove(dest_file)
		# Open file
		tech_file = open(dest_file, "w")
		# Write system info
		if self.sd_card:
			tech_file.write(
				"[PAYLOAD]\n" +
				"CPU frequency=" + f"{cpu_freq:.0f}" + "/" + f"{self.cpu_freq_max:.0f}" + " MHz\n" +
				"CPU usage=" + f"{cpu_usage:.0f}" + "/" + f"{self.cpu_usage_max:.0f}" + " %\n" +
				"CPU temperature=" + f"{cpu_temp:.1f}" + "/" + f"{self.cpu_temp_max:.1f}" + " degC\n" +
				"RAM usage=" + f"{mem_usage:.0f}" + "/" + f"{self.mem_usage_max:.0f}" + " %\n" +
				"Available space=" + f"{disk_free:.1f}" + " GB\n")
		else:
			tech_file.write(
				"[PAYLOAD]\n" +
				"CPU frequency=" + f"{cpu_freq:.0f}" + "/" + f"{self.cpu_freq_max:.0f}" + " MHz\n" +
				"CPU usage=" + f"{cpu_usage:.0f}" + "/" + f"{self.cpu_usage_max:.0f}" + " %\n" +
				"CPU temperature=" + f"{cpu_temp:.1f}" + "/" + f"{self.cpu_temp_max:.1f}" + " degC\n" +
				"RAM usage=" + f"{mem_usage:.0f}" + "/" + f"{self.mem_usage_max:.0f}" + " %\n")
		# Write power info
		tech_file.write(
			"[POWER]\n" +
			"PAYLOAD=" + f"{activity_percent:.0f}" + " %\n")
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
			error_dst_name = path + "share/technical.txt"
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
path = "./"
technical_driver = DriverTechnicalSystem()


# Manager
def manager(self):
	"""
		Running task
	"""

	global path

	# Trace
	trace_log(path, "TECH     > Activate")

	# Start timer
	self.timer.start_base_time(1.0)

	# Loop
	try:
		while True:

			# Read resource
			navigation = get_navigation(path)

			# Wait
			if self.step == USEA_PAYLOAD_STEP_IDLE:
				# Initiating descent
				if (
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_DECREASE) or
					(navigation == USEA_NAVIGATION_STATE_DESCENT)):
					# Trace
					trace_log(path, "TECH     > Start monitoring")
					# Reset counters
					self.diagnosis_reset()
					# Start recording
					self.step = USEA_PAYLOAD_STEP_RECORD

			# Navigation
			elif self.step == USEA_PAYLOAD_STEP_RECORD:
				# Navigation in progress
				if navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Start treatment
					self.step = USEA_PAYLOAD_STEP_TREAT

			# Treatment
			elif self.step == USEA_PAYLOAD_STEP_TREAT:
				# Sensor processing
				if not self.payload_step.read() == USEA_PAYLOAD_STEP_TREAT:
					# Trace
					trace_log(path, "TECH     > Stop monitoring")
					# Save diagnosis
					self.diagnosis_save()
					# Stop treatment
					self.step = USEA_PAYLOAD_STEP_IDLE

			# Wait
			else:
				time.sleep(0.1)

			# Monitoring rate
			if self.timer.is_tick():
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
		trace_log(path, "TECH     > [ERROR]")


# Test function
if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")
	path = "../"
	# Allocate resource
	technical = DriverTechnicalSystem()
	# Run
	technical.run()

#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	technical.py
	"""

# Standard libraries
import sys
import psutil
import traceback

# Project libraries
from system.timer_lib import *
from system.share_lib import *


# Class definition
class DriverTechnical:
	"""
		DriverTechnical class: system monitoring
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.step = USEA_PAYLOAD_STEP_IDLE
		self.timer = DriverTimer(path, "technical")
		# Counters
		self.activity_start = 0.0
		self.activity_run = 0.0
		self.cpu_usage_max = 0.0
		self.cpu_usage_sum = 0.0
		self.cpu_temp_max = 0.0
		self.cpu_temp_sum = 0.0
		self.mem_usage_max = 0.0
		self.mem_usage_sum = 0.0

	# Reset diagnosis counters
	def diagnosis_reset(self):
		"""
			Reset the diagnosis counters
			"""
		# Reset
		self.activity_start = datetime.datetime.now().timestamp()
		self.activity_run = 0.0
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
		self.activity_run = self.activity_run + 1.0
		# CPU usage
		cpu_usage = psutil.cpu_percent(interval=None)
		self.cpu_usage_sum = self.cpu_usage_sum + cpu_usage
		if cpu_usage > self.cpu_usage_max:
			self.cpu_usage_max = cpu_usage
		# CPU temperature
		cpu_temp = 0.0
		# TODO: cpu_temp = psutil.sensors_temperatures(fahrenheit=False)
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
		# CPU usage
		cpu_usage = self.cpu_usage_sum / self.activity_run
		# CPU temperature
		cpu_temp = self.cpu_temp_sum / self.activity_run
		# Memory usage
		mem_usage = self.mem_usage_sum / self.activity_run
		# Disk free
		disk_free = 0.0
		# TODO: disk_free = (psutil.disk_usage("/dev/sda1").total - psutil.disk_usage("/dev/sda1").used) / 1073741824.0
		# Create names
		dest_file = path + "payload/" + get_profile(path) + "_payload.txt"
		user_file = path + "share/technical.txt"
		# Remove dst file
		if os.path.isfile(dest_file):
			os.remove(dest_file)
		# Open file
		tech_file = open(dest_file, "w")
		# Write system info
		tech_file.write(
			"[PAYLOAD]\n" +
			"CPU=" + f"{cpu_usage:.0f}" + "/" + f"{self.cpu_usage_max:.0f}" + " %\n" +
			"RAM=" + f"{mem_usage:.0f}" + "/" + f"{self.mem_usage_max:.0f}" + " %\n" +
			"Tcpu=" + f"{cpu_temp:.1f}" + "/" + f"{self.cpu_temp_max:.1f}" + " degC\n" +
			"Available space=" + f"{disk_free:.1f}" + " GB\n")
		# Write power info
		tech_file.write(
			"[POWER]\n" +
			"Payload=" + f"{activity_percent:.0f}" + " %\n")
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


# Create resources
path = "./"
technical_driver = DriverTechnical()


# Manager
def manager(self):
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
				# Processing in progress
				if not navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
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
	"""
		Module test function
		"""
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")
	path = "../"
	# Allocate resource
	technical = DriverTechnical()
	# Run
	technical.run()

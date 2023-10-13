#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	timer_lib.py
	"""

# Standard libraries
import time
import threading

# Project libraries
from system.trace_lib import *

# Lock list
timer_locks = {}


# Class definition
class DriverTimer:
	"""
		DriverTimer class: software timer for tasks

		Attributes:
			- name (str): timer name

		Operations:
			- One-shot: once started, the timer will set its flag only once. It must be re-started after each count
			- Base-time: once started, the timer will set its flag after each base time completion.
	"""

	# Create resource
	def __init__(self, path: str, name: str):
		# Manager
		self.path = path
		self.name = name
		self.active = False
		self.one_shot = False
		self.duration = 0.0
		self.end = 0.0
		if name in timer_locks:
			return
		else:
			timer_locks[name] = threading.Lock()

	# Start (one-shot)
	def start_one_shot(self, interval: float):
		"""
			Start a one-shot timer for a specified interval of time (sec)

			Parameters:
				- interval (float): interval of time (sec)
			"""
		# Trace
		trace_log(self.path, "TIMER    > Start tmr_" + self.name + " one-shot " + str(interval) + " sec")
		# Wait for resource
		timer_locks[self.name].acquire()
		# Configure
		self.one_shot = True
		self.end = datetime.datetime.now().timestamp() + interval
		# Activate
		self.active = True
		# Release resource
		timer_locks[self.name].release()

	# Start (base time)
	def start_base_time(self, period: float):
		"""
			Start a timer with a specified base time (sec)

			Parameters:
				- period (float): base time (sec)
			"""
		# Trace
		trace_log(self.path, "TIMER    > Start tmr_" + self.name + " base time " + str(period) + " sec")
		# Wait for resource
		timer_locks[self.name].acquire()
		# Configure
		self.one_shot = False
		self.duration = period
		self.end = datetime.datetime.now().timestamp() + period
		# Activate
		self.active = True
		# Release resource
		timer_locks[self.name].release()

	# Stop
	def stop(self):
		"""
			Stop a timer
			"""
		# Trace
		trace_log(self.path, "TIMER    > Stop tmr_" + self.name)
		# Wait for resource
		timer_locks[self.name].acquire()
		# Deactivate
		self.active = False
		# Release resource
		timer_locks[self.name].release()

	# Test timer
	def is_tick(self) -> bool:
		"""
			Test if the specified timer period has elapsed

			Returns:
				- bool: True if the time period has elapsed
			"""
		# Wait for resource
		timer_locks[self.name].acquire()
		# Activated
		if self.active:
			# Get result
			if datetime.datetime.now().timestamp() < self.end:
				result = False
			else:
				# Reload duration
				if not self.one_shot:
					self.end = self.end + self.duration
				# Result
				result = True
		# Deactivated
		else:
			result = False
		# Release resource
		timer_locks[self.name].release()
		# Result
		return result

	# Wait for a duration
	def wait_until_duration(self, duration: float):
		"""
			Wait for a specified interval of time (sec)

			Parameters:
				- duration (float): time duration (sec)
			"""
		# Trace
		trace_log(self.path, "TIMER    > Wait tmr_" + self.name + " " + str(duration) + " sec")
		# Wait for resource
		timer_locks[self.name].acquire()
		# Activate
		self.active = True
		# Configure
		self.end = datetime.datetime.now().timestamp() + duration
		# Wait loop
		while True:
			# Compute remaining time
			remaining = self.end - datetime.datetime.now().timestamp()
			# Close to the end ?
			if remaining > 1.5:
				time.sleep(1.0)
			# Test
			if remaining <= 0.0:
				break
		# Deactivate
		self.active = False
		# Release resource
		timer_locks[self.name].release()

	# Wait for a date
	def wait_until_date(self, date: str):
		"""
			Wait until an exact date/time

			Parameters:
				- date (str): date and time ("YY-MM-DD HH:MM:SS" format)
			"""
		# Trace
		trace_log(self.path, "TIMER    > Wait tmr_" + self.name + " " + date)
		# Wait for resource
		timer_locks[self.name].acquire()
		# Extract date
		date_time = datetime.datetime.strptime(date, "%y-%m-%d %H:%M:%S")
		# Activate
		self.active = True
		# Configure
		self.end = date_time.timestamp()
		# Wait loop
		while True:
			# Compute remaining time
			remaining = self.end - datetime.datetime.now().timestamp()
			# Close to the end ?
			if remaining > 1.5:
				time.sleep(1.0)
			# Test
			if remaining <= 0.0:
				break
		# Deactivate
		self.active = False
		# Release resource
		timer_locks[self.name].release()

	# Wait synchronization
	def wait_until_synchro(self):
		"""
			Wait until the current second to change
			"""
		# Trace
		trace_log(self.path, "TIMER    > Synchro tmr_" + self.name + " ")
		# Wait for resource
		timer_locks[self.name].acquire()
		# Activate
		self.active = True
		# Configure
		end = datetime.datetime.now()
		# Wait loop
		while end.second == datetime.datetime.now().second:
			continue
		# Deactivate
		self.active = False
		# Release resource
		timer_locks[self.name].release()

	# Get remaining time
	def remaining_time(self) -> float:
		"""
			Get the remaining time before next timer tick

			Returns:
				- float: remaining time (sec)
			"""
		# Wait for resource
		timer_locks[self.name].acquire()
		# Compute remaining time
		remaining = self.end - datetime.datetime.now().timestamp()
		# Integrity test
		if remaining < 0.0:
			# Elapsed
			remaining = 0
			# Deactivate
			if self.one_shot:
				self.active = False
		# Activated ?
		if not self.active:
			remaining = -1
		# Release resource
		timer_locks[self.name].release()
		# Result
		return remaining

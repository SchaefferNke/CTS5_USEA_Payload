#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	timer_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2023-11-06"
__version__ = "1.0.0"

# Standard libraries
import time
import datetime
import threading

# Project libraries
from system.trace_lib import trace_log

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
		self._path = path
		self._name = name
		self._active = False
		self._one_shot = False
		self._duration = 0.0
		self._end = 0.0
		if not name in timer_locks:
			timer_locks[name] = threading.Lock()

	# Start (one-shot)
	def start_one_shot(self, interval: float):
		"""
			Start a one-shot timer for a specified interval of time (sec)

			Parameters:
				- interval (float): interval of time (sec)
		"""
		# Trace
		#trace_log(self._path, "TIMER    > Start tmr_" + self._name + " one-shot " + str(interval) + " sec")
		# Wait for resource
		timer_locks[self._name].acquire()
		# Configure
		self._one_shot = True
		self._end = datetime.datetime.now().timestamp() + interval
		# Activate
		self._active = True
		# Release resource
		timer_locks[self._name].release()

	# Start (base time)
	def start_base_time(self, period: float):
		"""
			Start a timer with a specified base time (sec)

			Parameters:
				- period (float): base time (sec)
		"""
		# Trace
		#trace_log(self._path, "TIMER    > Start tmr_" + self._name + " base time " + str(period) + " sec")
		# Wait for resource
		timer_locks[self._name].acquire()
		# Configure
		self._one_shot = False
		self._duration = period
		self._end = datetime.datetime.now().timestamp() + period
		# Activate
		self._active = True
		# Release resource
		timer_locks[self._name].release()

	# Stop
	def stop(self):
		"""
			Stop a timer
		"""
		# Trace
		trace_log(self._path, "TIMER    > Stop tmr_" + self._name)
		# Wait for resource
		timer_locks[self._name].acquire()
		# Deactivate
		self._active = False
		# Release resource
		timer_locks[self._name].release()

	# Test timer
	def is_tick(self) -> bool:
		"""
			Test if the specified timer period has elapsed

			Returns:
				- bool: True if the time period has elapsed
		"""
		# Wait for resource
		timer_locks[self._name].acquire()
		# Activated
		if self._active:
			# Get result
			if datetime.datetime.now().timestamp() < self._end:
				# Result
				result = False
			else:
				# One-shot mode
				if self._one_shot:
					# Deactivate
					self._active = False
				# Base-time mode
				else:
					# Compute next time
					while datetime.datetime.now().timestamp() >= self._end:
						self._end = self._end + self._duration
				# Result
				result = True
		# Deactivated
		else:
			# Result
			result = False
		# Release resource
		timer_locks[self._name].release()
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
		trace_log(self._path, "TIMER    > Wait tmr_" + self._name + " " + str(duration) + " sec")
		# Wait for resource
		timer_locks[self._name].acquire()
		# Activate
		self._active = True
		# Configure
		self._end = datetime.datetime.now().timestamp() + duration
		# Wait loop
		while True:
			# Compute remaining time
			remaining = self._end - datetime.datetime.now().timestamp()
			# Close to the end ?
			if remaining > 1.5:
				time.sleep(1.0)
			# Test
			if remaining <= 0.0:
				break
		# Deactivate
		self._active = False
		# Release resource
		timer_locks[self._name].release()

	# Wait for a date
	def wait_until_date(self, date: str):
		"""
			Wait until an exact date/time

			Parameters:
				- date (str): date and time ("YY-MM-DD HH:MM:SS" format)
		"""
		# Trace
		trace_log(self._path, "TIMER    > Wait tmr_" + self._name + " " + date)
		# Wait for resource
		timer_locks[self._name].acquire()
		# Extract date
		date_time = datetime.datetime.strptime(date, "%y-%m-%d %H:%M:%S")
		# Activate
		self._active = True
		# Configure
		self._end = date_time.timestamp()
		# Wait loop
		while True:
			# Compute remaining time
			remaining = self._end - datetime.datetime.now().timestamp()
			# Close to the end ?
			if remaining > 1.5:
				time.sleep(1.0)
			# Test
			if remaining <= 0.0:
				break
		# Deactivate
		self._active = False
		# Release resource
		timer_locks[self._name].release()

	# Wait synchronization
	def wait_until_synchro(self):
		"""
			Wait until the current second to change
		"""
		# Trace
		trace_log(self._path, "TIMER    > Synchro tmr_" + self._name)
		# Wait for resource
		timer_locks[self._name].acquire()
		# Activate
		self._active = True
		# Configure
		end = datetime.datetime.now()
		# Wait loop
		while end.second == datetime.datetime.now().second:
			continue
		# Deactivate
		self._active = False
		# Release resource
		timer_locks[self._name].release()

	# Get remaining time
	def remaining_time(self) -> float:
		"""
			Get the remaining time before next timer tick

			Returns:
				- float: remaining time (sec)
		"""
		# Wait for resource
		timer_locks[self._name].acquire()
		# Compute remaining time
		remaining = self._end - datetime.datetime.now().timestamp()
		# Integrity test
		if remaining < 0.0:
			# Elapsed
			remaining = 0
			# Deactivate
			if self._one_shot:
				self._active = False
		# Activated ?
		if not self._active:
			remaining = -1
		# Release resource
		timer_locks[self._name].release()
		# Result
		return remaining

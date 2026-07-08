#!/bin/python
# -*- coding: utf-8 -*-
"""
	timer_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-07-03"
__version__ = "1.0.2"

# Standard libraries
import time
import datetime
import threading

# Project libraries
from system.trace_lib import trace_log
from system.share_lib import FileShare

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
	def __init__(self, name: str):
		# Manager
		self._name = name
		self._active = False
		self._one_shot = False
		self._duration = 0.0
		self._start = 0.0
		self._stop = 0.0
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
		# trace_log("TIMER    > Start tmr_" + self._name + " one-shot " + str(interval) + " sec")
		# Wait for resource
		timer_locks[self._name].acquire()
		# Try
		try:
			# Configure
			self._one_shot = True
			self._start = datetime.datetime.now().timestamp()
			self._stop = self._start + interval
			# Activate
			self._active = True
		# Exit
		finally:
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
		trace_log("TIMER    > Start tmr_" + self._name + " base time " + str(period) + " sec")
		# Wait for resource
		timer_locks[self._name].acquire()
		# Try
		try:
			# Configure
			self._one_shot = False
			self._duration = period
			self._start = datetime.datetime.now().timestamp()
			self._stop = self._start + period
			# Activate
			self._active = True
		# Exit
		finally:
			# Release resource
			timer_locks[self._name].release()

	# Stop
	def stop(self):
		"""
			Stop a timer
		"""
		# Trace
		trace_log("TIMER    > Stop tmr_" + self._name)
		# Wait for resource
		timer_locks[self._name].acquire()
		# Try
		try:
			# Deactivate
			self._active = False
		# Exit
		finally:
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
		# Try
		try:
			# Activated
			if not self._active:
				# Result
				return False
			# Resynchronize
			self._after_external_clock_synchronization()
			# Get result
			if datetime.datetime.now().timestamp() < self._stop:
				# Result
				return False
			# One-shot mode
			if self._one_shot:
				# Deactivate
				self._active = False
			# Base-time mode
			else:
				# Compute next time
				while datetime.datetime.now().timestamp() >= self._stop:
					self._stop += self._duration
			# Result
			return True
		# Exit
		finally:
			# Release resource
			timer_locks[self._name].release()

	# Wait for a duration
	def wait_until_duration(self, duration: float):
		"""
			Wait for a specified interval of time (sec)

			Parameters:
				- duration (float): time duration (sec)
		"""
		# Trace
		trace_log("TIMER    > Wait tmr_" + self._name + " " + str(duration) + " sec")
		# Wait for resource
		timer_locks[self._name].acquire()
		# Try
		try:
			# Activate
			self._active = True
			# Configure
			self._stop = datetime.datetime.now().timestamp() + duration
			# Wait loop
			while True:
				# Resynchronize
				self._after_external_clock_synchronization()
				# Compute remaining time
				remaining = self._stop - datetime.datetime.now().timestamp()
				# Test
				if remaining <= 0.0:
					break
				# Close to the end ?
				if remaining > 1.5:
					time.sleep(1.0)
				else:
					time.sleep(0.001)
			# Deactivate
			self._active = False
		# Exit
		finally:
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
		trace_log("TIMER    > Wait tmr_" + self._name + " " + date)
		# Wait for resource
		timer_locks[self._name].acquire()
		# Try
		try:
			# Extract date
			date_time = datetime.datetime.strptime(date, "%y-%m-%d %H:%M:%S")
			# Activate
			self._active = True
			# Configure
			self._stop = date_time.timestamp()
			# Wait loop
			while True:
				# Resynchronize
				self._after_external_clock_synchronization()
				# Compute remaining time
				remaining = self._stop - datetime.datetime.now().timestamp()
				# Test
				if remaining <= 0.0:
					break
				# Close to the end ?
				if remaining > 1.5:
					time.sleep(1.0)
				else:
					time.sleep(0.001)
			# Deactivate
			self._active = False
		# Exit
		finally:
			# Release resource
			timer_locks[self._name].release()

	# Wait synchronization
	def wait_until_synchro(self):
		"""
			Wait until the current second to change
		"""
		# Trace
		trace_log("TIMER    > Synchro tmr_" + self._name)
		# Wait for resource
		timer_locks[self._name].acquire()
		# Try
		try:
			# Activate
			self._active = True
			# Configure
			end = datetime.datetime.now()
			# Wait loop
			while end.second == datetime.datetime.now().second:
				time.sleep(0.001)
				continue
			# Deactivate
			self._active = False
		# Exit
		finally:
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
		# Try
		try:
			# Compute remaining time
			remaining = self._stop - datetime.datetime.now().timestamp()
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
			# Result
			return remaining
		# Exit
		finally:
			# Release resource
			timer_locks[self._name].release()

	# Resynchronize timers after external clock synchronization
	def _after_external_clock_synchronization(self):
		"""
			Resynchronize timers after external clock synchronization

			Parameters:
				- timer (DriverTimer): timer to synchronize
		"""
		# Read shared information
		try:
			share = FileShare("synchro.txt")
			share.read()
		except (FileNotFoundError, OSError):
			return
		# Try
		try:
			# External synchronisation ?
			if share.content.string not in ("", "?"):
				# Compute new start
				new_start = share.content.timestamp
				# New start ?
				if new_start != self._start:
					# Now
					now = datetime.datetime.now().timestamp()
					# Try to compute delta
					try:
						delta = float(share.content.string)
					except (ValueError, TypeError):
						return
					# Compute remaining time
					remaining = self._stop - now - delta
					# Update timer
					self._start = new_start
					self._stop = now + remaining
					# Trace
					trace_log("TIMER    > Restart tmr_" + self._name + " (" + f"{remaining:.1f}" + " sec)")
		# Error
		except (AttributeError, ValueError):
			return

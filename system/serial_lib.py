#!/bin/python
# -*- coding: utf-8 -*-
"""
	serial_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-02-11"
__version__ = "1.0.1"

# Standard libraries
import serial
import threading

# Project libraries
from system.system_lib import system_driver

# Lock list
serial_locks = {}


# Class definition
class DriverSerial:
	"""
		DriverSerial class: serial port resource access for tasks

		Attributes:
			- name (str): name (eg: "COM_1")
			- speed (int): baud rate (eg: 57600 bauds)
			- timeout (float): reading timeout (sec)

		Access modes (exclusive):
			- persistent : open/read/write/close
			- oneshot    : receive_ascii

		Important:
			When the serial port is opened in persistent mode, the serial resource and the associated lock are held
			exclusively until close() is explicitly called.
			open() must be paired with close() to release the lock and the resource.
	"""

	MODE_NONE = None
	MODE_PERSISTENT = "persistent"
	MODE_ONESHOT = "oneshot"

	# Create resource
	def __init__(self, name: str, speed: int, timeout: float):
		# Manager
		self._name = system_driver.format_serial_name(name)
		self._speed = speed
		self._timeout = timeout
		self._serial = None
		self._mode = self.MODE_NONE
		if not self._name in serial_locks:
			serial_locks[self._name] = threading.Lock()

	# Open serial port (persistent mode)
	def open(self) -> bool:
		"""
			Open the serial port

			Returns:
				- bool: True if the port is open
		"""
		# Integrity test
		if self._mode == self.MODE_ONESHOT:
			raise RuntimeError("Serial port already used in oneshot mode")
		# Select resource
		lock = serial_locks[self._name]
		# Wait for resource
		lock.acquire()
		# Try
		try:
			# Open
			self._serial = serial.Serial(self._name, self._speed, timeout=self._timeout)
			# Flush serial port
			self._serial.reset_input_buffer()
			self._serial.reset_output_buffer()
			# Select mode
			self._mode = self.MODE_PERSISTENT
			# Result
			return self._serial.is_open
		# Access fail
		except (serial.SerialException, ValueError, OSError, PermissionError):
			# Release object
			self._serial = None
			self._mode = self.MODE_NONE
			# Release resource
			lock.release()
			# Error
			return False

	# Close serial port
	def close(self):
		"""
			Close the serial port
		"""
		# Integrity test
		if self._mode != self.MODE_PERSISTENT:
			return
		try:
			# Close serial port
			if self._serial and self._serial.is_open:
				self._serial.close()
		finally:
			# Release object
			self._serial = None
			self._mode = self.MODE_NONE
			# Release resource
			serial_locks[self._name].release()

	# Get the number of bytes in the input buffer
	def in_waiting(self) -> int:
		"""
			Get the number of bytes in the input buffer

			Returns:
				- int: number of bytes in the reception buffer
		"""
		# Integrity test
		if self._mode != self.MODE_PERSISTENT:
			raise RuntimeError("Serial port not in persistent mode")
		# Error
		if not self._serial or not self._serial.is_open:
			return 0
		# Result
		return self._serial.in_waiting

	# Read size bytes from the serial port
	def read(self, size: int) -> bytes:
		"""
			Read size bytes from the serial port

			Parameters:
				- size (int): number of bytes to read

			Returns:
				- bytes: bytes read from the serial port
		"""
		# Integrity test
		if self._mode != self.MODE_PERSISTENT:
			raise RuntimeError("Serial port not in persistent mode")
		# Error
		if not self._serial or not self._serial.is_open:
			return b""
		# Result
		return self._serial.read(size)

	# Write the bytes data to the port
	def write(self, data: bytes) -> int:
		"""
			Write the bytes data to the serial port

			Parameters:
				- data (bytes): data to send

			Returns:
				- int: number of bytes written
		"""
		# Integrity test
		if self._mode != self.MODE_PERSISTENT:
			raise RuntimeError("Serial port not in persistent mode")
		# Error
		if not self._serial or not self._serial.is_open:
			return 0
		# Result
		return self._serial.write(data)

	# Receive frame
	def receive_ascii(self, timeout: float) -> str:
		"""
			ASCII frame reception process

			Parameters:
				- timeout (float): waiting time

			Returns:
				- str: bytes read from the serial port or "?" if a timeout/error occurs
		"""
		# Integrity test
		if self._mode == self.MODE_PERSISTENT:
			raise RuntimeError("Serial port already opened in persistent mode")
		# Wait for resource
		with serial_locks[self._name]:
			# Select mode
			self._mode = self.MODE_ONESHOT
			try:
				# Open serial port
				with serial.Serial(self._name, self._speed, timeout=timeout) as ser:
					# Flush serial port
					ser.reset_input_buffer()
					# Read until newline
					buffer = ser.read_until(b"\n")
					# Timeout
					if not buffer:
						return "?"
					# Decode
					frame_rx = buffer.decode("ascii", errors="ignore")
					# Result
					return frame_rx.rstrip("\r\n")
			# Serial port error
			except serial.SerialException:
				return "?"
			# Reset mode
			finally:
				self._mode = self.MODE_NONE

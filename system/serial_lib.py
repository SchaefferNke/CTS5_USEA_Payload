#!/bin/python
# -*- coding: utf-8 -*-
"""
	serial_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-05-13"
__version__ = "1.0.0"

# Standard libraries
import datetime
import serial
import threading
import traceback

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
			- size (int): read buffer size
			- timeout (float): reading timeout (sec)
	"""

	# Create resource
	def __init__(self, name: str, speed: int, size: int, timeout: float):
		# Manager
		self._name = system_driver.format_serial_name(name)
		self._speed = speed
		self._size = size
		self._timeout = timeout
		self._serial = None
		if not self._name in serial_locks:
			serial_locks[self._name] = threading.Lock()

	# Open serial port
	def open(self) -> bool:
		"""
			Open the serial port

			Returns:
				- bool: True if the port is open
		"""
		# Wait for resource
		serial_locks[self._name].acquire()
		# Open
		self._serial = serial.Serial(self._name, self._speed, timeout=self._timeout)
		# Flush serial port
		self._serial.flushInput()
		self._serial.flushOutput()
		# Open
		if self._serial.isOpen():
			return True
		# Release resource
		serial_locks[self._name].release()
		# Error
		return False

	# Close serial port
	def close(self):
		"""
			Close the serial port
		"""
		# Close serial port
		self._serial.close()
		# Release resource
		serial_locks[self._name].release()

	# Get the number of bytes in the input buffer
	def in_waiting(self) -> int:
		"""
			Get the number of bytes in the input buffer

			Returns:
				- int: number of bytes in the reception buffer
		"""
		# Result
		return self._serial.in_waiting

	# Read size bytes from the serial port
	def read(self, size: int) -> bytes:
		"""
			Read size bytes from the serial port

			Parameters:
				- size (int): number of bytes to read

			Returns:
				- int: bytes read from the serial port
		"""
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
		# Result
		return self._serial.write(data)

	# Receive frame
	def receive_ascii(self, timeout: float) -> str:
		"""
			ASCII frame reception process

			Parameters:
				- timeout (float): waiting time

			Returns:
				- str: bytes read from the serial port
		"""
		# Initialize
		frame_rx = ""
		# Wait for resource
		serial_locks[self._name].acquire()
		# Open
		self._serial = serial.Serial(self._name, self._speed, timeout=self._timeout)
		# Flush serial port
		self._serial.flushInput()
		self._serial.flushOutput()
		# Initialize time-out
		timeout = datetime.datetime.now().timestamp() + timeout
		# Acquisition loop
		if self._serial.isOpen():
			try:
				# Reception process
				while True:
					# Time out
					if datetime.datetime.now().timestamp() >= timeout:
						# Close serial port
						self._serial.close()
						# Release resource
						serial_locks[self._name].release()
						# Exit
						return ""
					# Wait character
					if self._serial.in_waiting == 0:
						continue
					# Read frame
					frame_rx = self._serial.read(self._size).decode()
					# Check end of line
					if frame_rx[-2] != "\r":
						continue
					# Extract data
					frame_rx = frame_rx[0:-2]
					# Exit
					break
			# Error
			except Exception as err:
				# Trace
				print(err)
				print(traceback.format_exc())
		# Close serial port
		self._serial.close()
		# Release resource
		serial_locks[self._name].release()
		# Result
		return frame_rx

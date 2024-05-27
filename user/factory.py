#!/bin/python
# -*- coding: utf-8 -*-
"""
	factory.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-05-27"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import time

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.rtc import DriverRTC
from system.io_lib import DriverIOOutput, DriverIOInput
from system.serial_lib import DriverSerial


# Class definition
class DriverFactory:
	"""
		DriverFactory class: test hardware resources
	"""

	# Create resource
	def __init__(self):
		# Hardware resource
		self._resource = ""

	# Test output
	def test_output(self, name: str, value: str):
		"""
			Output test sequence

			Parameters:
				- name (str): IO name (eg: "GPIO_3_8")
				- value (str): "0/1"
		"""
		self._resource = DriverIOOutput(name)
		if value == "1":
			print("Output\t" + name + "\t= on")
			self._resource.set_on()
		else:
			print("Output\t" + name + "\t= off")
			self._resource.set_off()

	# Test input
	def test_input(self, name: str):
		"""
			Input test sequence

			Parameters:
				- name (str): IO name (eg: "GPIO_3_4")
		"""
		self._resource = DriverIOInput(name)
		if self._resource.is_on():
			print("Input\t" + name + "\t= on")
		else:
			print("Input\t" + name + "\t= off")

	# Test serial port
	def test_serial(self, name: str):
		"""
			Serial port test sequence

			Parameters:
				- name (str): Serial port name (eg: "COM_1")
		"""
		try:
			self._resource = DriverSerial(name, 9600, 32, 0.15)
			self._resource.open()
			self._resource.write("Test".encode("ascii"))
			result = self._resource.read(32).decode()
			self._resource.close()
			if result == "Test":
				print("Serial\t" + name + "\t\t= success")
			else:
				print("Serial\t" + name + "\t\t= error")

		except Exception:
			print("Serial\t" + name + "\t\t= not available")

	# Test I2C
	def test_i2c(self, name: str):
		"""
			I2C port test sequence

			Parameters:
				- name (str): I2C port name (eg: "I2C_1")
		"""
		# TODO: to implement
		print("I2C\t" + name + "\t\t= not implemented")

	# Test SPI
	def test_spi(self, name: str):
		"""
			SPI port test sequence

			Parameters:
				- name (str): SPI port name (eg: "SPI_4")
		"""
		# TODO: to implement
		print("SPI\t" + name + "\t\t= not implemented")

	# Test SD card
	def test_disk2(self, name: str):
		"""
			SD card test sequence

			Parameters:
				- name (str): SD card name (eg: "MMC_0")
		"""
		try:
			test_file = "/media/sd/test.txt"
			if os.path.isfile(test_file):
				os.remove(test_file)
			self._resource = open(test_file, "w")
			self._resource.write("Writing test\n")
			self._resource.close()
			print("SD\t" + name + "\t\t= success")

		except Exception:
			print("SD\t" + name + "\t\t= not available")

	# Test RTC
	def test_rtc(self, name: str):
		"""
			RTC test sequence

			Parameters:
				- name (str): RTC name (eg: "RTC_0")
		"""
		try:
			self._resource = DriverRTC()
			self._resource.restore()
			print("RTC\t" + name + "\t\t= success")

		except Exception:
			print("RTC\t" + name + "\t\t= not available")

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Scheduler
		manager(self)


# Create resources
factory_driver = DriverFactory()


# Manager
def manager(self):
	"""
		Running task
	"""

	# RTC
	factory_driver.test_rtc("RTC_0")
	# SLEEPN
	factory_driver.test_output("GPIO_3_27", "1")
	# DEV2_6
	factory_driver.test_output("GPIO_3_3", "0")
	# CSV2_1 (expansion connector E2)
	factory_driver.test_output("GPIO_2_15", "0")
	# CSV2_2 (expansion connector E2)
	factory_driver.test_output("GPIO_3_28", "0")
	# ioV2_1 (expansion connector E2)
	factory_driver.test_output("GPIO_3_13", "0")
	# ioV2_2 (expansion connector E2)
	factory_driver.test_output("GPIO_3_14", "0")
	# CMDV2_1
	factory_driver.test_output("GPIO_3_8", "1")
	# CMDV2_2
	factory_driver.test_output("GPIO_3_17", "1")
	# CMDV2_3
	factory_driver.test_output("GPIO_3_25", "1")
	# CMDV2_4
	factory_driver.test_output("GPIO_3_19", "1")
	# CMDV2_5
	factory_driver.test_output("GPIO_3_20", "1")
	# CMDV2_6
	factory_driver.test_output("GPIO_3_23", "1")
	# CMDV2_7 (expansion connector E2)
	factory_driver.test_output("GPIO_3_24", "1")
	# ALARMS_1
	factory_driver.test_input("GPIO_3_4")
	# ALARMS_2
	factory_driver.test_input("GPIO_3_0")
	# ALARMS_3
	factory_driver.test_input("GPIO_1_10")
	# ALARMS_4
	factory_driver.test_input("GPIO_1_0")
	# ALARMS_5
	factory_driver.test_input("GPIO_5_5")
	# ALARMS_6
	factory_driver.test_input("GPIO_5_9")
	# ALARMS_7 (expansion connector E2)
	factory_driver.test_input("GPIO_3_2")
	# RXV2_1, TXV2_1
	factory_driver.test_serial("COM_1")
	# RXV2_2, TXV2_2
	factory_driver.test_serial("COM_2")
	# RXV2_3, TXV2_3
	factory_driver.test_serial("COM_3")
	# RXV2_4, TXV2_4
	factory_driver.test_serial("COM_4")
	# RXV2_5, TXV2_5
	factory_driver.test_serial("COM_5")
	# RXV2_6, TXV2_6
	factory_driver.test_serial("COM_6")
	# I2CV2 (expansion connector E2)
	factory_driver.test_i2c("I2C_1")
	# SPIV2 (expansion connector E2)
	factory_driver.test_spi("SPI_4")
	# SD card access (uSD card slot SD1)
	factory_driver.test_disk2("MMC_0")


# Test function
if __name__ == "__main__":
	# Run
	factory_driver.run()

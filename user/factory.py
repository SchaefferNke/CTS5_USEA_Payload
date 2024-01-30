#!/bin/python
# -*- coding: utf-8 -*-
"""
	factory.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-01-29"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import time

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
	def test_output(self, name: str):
		"""
			Output test sequence

			Parameters:
				- name (str): IO name (eg: "GPIO_3_8")
		"""
		self._resource = DriverIOOutput(name)
		print("Output\t" + name + "\t= on")
		self._resource.set_on()
		time.sleep(0.5)
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
		print("I2C\t\t" + name + "\t\t= not implemented")

	# Test SPI
	def test_spi(self, name: str):
		"""
			SPI port test sequence

			Parameters:
				- name (str): SPI port name (eg: "SPI_4")
		"""
		# TODO: to implement
		print("SPI\t\t" + name + "\t\t= not implemented")

	# Test SD
	def test_sd(self, name: str):
		"""
			SD port test sequence

			Parameters:
				- name (str): SD port name (eg: "SD_1")
		"""
		# TODO: to implement
		print("SD\t\t" + name + "\t\t= not implemented")

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
			print("RTC\t\t" + name + "\t\t= success")

		except Exception:
			print("RTC\t\t" + name + "\t\t= not available")


# Test function
if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")
	# Allocate resource
	factory = DriverFactory()
	# INTV2
	factory.test_input("GPIO_5_8")
	# SLEEPN
	factory.test_output("GPIO_3_27")
	# DEV2_6
	factory.test_output("GPIO_3_3")
	# CSV2_1 (expansion connector E2)
	factory.test_output("GPIO_2_15")
	# CSV2_2 (expansion connector E2)
	factory.test_output("GPIO_3_28")
	# ioV2_1 (expansion connector E2)
	factory.test_output("GPIO_3_13")
	# ioV2_2 (expansion connector E2)
	factory.test_output("GPIO_3_14")
	# PPS
	factory.test_input("GPIO_4_14")
	# SD_CD (uSD card slot SD1)
	factory.test_input("GPIO_1_19")
	# CMDV2_1
	factory.test_output("GPIO_3_8")
	# CMDV2_2
	factory.test_output("GPIO_3_17")
	# CMDV2_3
	factory.test_output("GPIO_3_25")
	# CMDV2_4
	factory.test_output("GPIO_3_19")
	# CMDV2_5
	factory.test_output("GPIO_3_20")
	# CMDV2_6
	factory.test_output("GPIO_3_23")
	# CMDV2_7 (expansion connector E2)
	factory.test_output("GPIO_3_24")
	# ALARMS_1
	factory.test_input("GPIO_3_4")
	# ALARMS_2
	factory.test_input("GPIO_3_0")
	# ALARMS_3
	factory.test_input("GPIO_2_2")
	# ALARMS_4
	factory.test_input("GPIO_2_7")
	# ALARMS_5
	factory.test_input("GPIO_2_0")
	# ALARMS_6
	factory.test_input("GPIO_2_1")
	# ALARMS_7 (expansion connector E2)
	factory.test_input("GPIO_3_2")
	# RXV2_1, TXV2_1
	factory.test_serial("COM_1")
	# RXV2_2, TXV2_2
	factory.test_serial("COM_2")
	# RXV2_3, TXV2_3
	factory.test_serial("COM_3")
	# RXV2_4, TXV2_4
	factory.test_serial("COM_4")
	# RXV2_5, TXV2_5
	factory.test_serial("COM_5")
	# RXV2_6, TXV2_6
	factory.test_serial("COM_6")
	# RXV2_7, TXV2_7 (expansion connector E2)
	factory.test_serial("COM_7")
	# RXV2_8, TXV2_8
	factory.test_serial("COM_8")
	# I2CV2 (expansion connector E2)
	factory.test_i2c("I2C_1")
	# SPIV2 (expansion connector E2)
	factory.test_spi("SPI_4")
	# SD card access (uSD card slot SD1)
	factory.test_sd("USDHC_1")
	# RTC
	factory.test_rtc("RTC_0")

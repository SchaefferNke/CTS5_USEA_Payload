#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	sensor.py
	"""

# Standard libraries
import sys
import os

# Project libraries
from system.const import *
from system.io_lib import *
from system.serial_lib import *
from system.timer_lib import *
from system.share_lib import *

global path


# Acquisition process
def acquisition_process(self, string: str) -> bool:
	"""
		Sample acquisition process

		Returns:
			- bool: True if the acquisition process is successful
		"""
	# Print
	trace_log(path, "SENSOR   > " + string)
	# Power-on
	self.power_io.set_on()
	# Warm-up
	time.sleep(3.5)
	# Acquisition
	frame_data = self.serial.receive_ascii(3.0)
	# Treatment
	if "SENSO,D," in frame_data[0:8]:
		# Parse
		split = frame_data.split(",")
		# Print
		trace_log(path, "SENSOR   > Rx=" + frame_data)
		# Extract
		self.output.timestamp = datetime.datetime.now().timestamp()
		self.output.channel1 = float(split[2])
		self.output.channel2 = float(split[3])
		self.output.channel3 = float(split[4])
		# Result
		result = True
	# Error
	else:
		# Print
		trace_log(path, "SENSOR   > Time-out")
		# Result
		result = False
	# Power-off
	self.power_io.set_off()
	# Delay before new power-on (for proper operation of the sensor)
	time.sleep(0.5)
	# Result
	return result


# Output definition
class DataSensor:
	"""
		DataSensor class: sensor sample

		Attributes:
			- timestamp (float): timestamp
			- channel1 (float): channel 1 raw value
			- channel2 (float): channel 2 raw value
			- channel3 (float): channel 3 raw value
		"""

	# Output
	def __init__(self):
		self.timestamp = 0.0
		self.channel1 = 0.0
		self.channel2 = 0.0
		self.channel3 = 0.0


# Class definition
class DriverSensor:
	"""
		Driver_sensor class
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.active = False
		self.step = USEA_SENSOR_STEP_IDLE
		self.power_io = DriverIO("OUT5")
		self.serial = DriverSerial("COM5", 19200, 128, 0.15)
		self.timer = DriverTimer(path, "sensor")
		self.share_data = FileShare(path, "sensor.txt")
		self.share_step = DataShare("sensor_step")
		# Output
		self.output = DataSensor()
		self.output.timestamp = 0.0
		self.output.channel1 = 0.0
		self.output.channel2 = 0.0
		self.output.channel3 = 0.0

	# Get next task activity
	def time_before_activity(self) -> float:
		"""
			Get the time remaining before the next task activity

			Returns:
				- float: time remaining before the next task activity (sec)
			"""
		# Waiting for the next measurement
		if not self.active:
			result = -1.0
		elif self.step == USEA_SENSOR_STEP_RECORD:
			result = self.timer.remaining_time()
		else:
			result = 0.0
		# Result
		return result

	# Run task
	def run(self):
		"""
			Working task
			"""
		# Scheduler
		manager(self)

	# Acquire data
	def acquire_sample(self) -> bool:
		"""
			Sample acquisition process

			Returns:
				- bool: True if the acquisition process is successful
			"""
		# Acquire
		return acquisition_process(self, "Acquire")


# Class definition
class TestSensor:
	"""
		Test_sensor class
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.power_io = DriverIO("OUT5")
		self.serial = DriverSerial("COM5", 19200, 128, 0.15)
		# Output
		self.output = DataSensor()
		self.output.timestamp = 0.0
		self.output.channel1 = 0.0
		self.output.channel2 = 0.0
		self.output.channel3 = 0.0

	# Test sensor
	def test(self) -> bool:
		"""
			Test process

			Returns:
				- bool: True if the test process is successful
			"""
		# Acquire
		return acquisition_process(self, "Test")


# Create resources
path = "./"
sensor_driver = DriverSensor()


# Manager
def manager(self):
	global path

	# Trace
	trace_log(path, "SENSOR   > Activate")

	# Activate task
	self.active = True
	# Synchronize timer
	self.timer.wait_until_synchro()
	# Start timer
	self.timer.start_base_time(10.0)
	# Share step
	self.share_step.write(self.step)

	# Loop
	try:
		while True:

			# Sensor activated ?
			if not self.active:
				time.sleep(0.1)
				continue

			# Read resource
			navigation = get_navigation(path)

			# Wait
			if self.step == USEA_SENSOR_STEP_IDLE:
				# Ascent step
				if ((navigation == USEA_NAVIGATION_STATE_ASCENT)
				 or (navigation == USEA_NAVIGATION_STATE_ASCENT_1)
				 or (navigation == USEA_NAVIGATION_STATE_ASCENT_2)
				 or (navigation == USEA_NAVIGATION_STATE_ASCENT_3)):
					# Create file name
					filename = path + "payload/" + get_profile(path) + "_payload.csv"
					# Print
					trace_log(path, "SENSOR   > Start acquisition")
					# Start recording
					self.step = USEA_SENSOR_STEP_RECORD
					# Share step
					self.share_step.write(self.step)
				# Wait
				else:
					time.sleep(0.1)

			# Record
			elif self.step == USEA_SENSOR_STEP_RECORD:
				# Ascent step
				if ((navigation == USEA_NAVIGATION_STATE_ASCENT)
				 or (navigation == USEA_NAVIGATION_STATE_ASCENT_1)
				 or (navigation == USEA_NAVIGATION_STATE_ASCENT_2)
				 or (navigation == USEA_NAVIGATION_STATE_ASCENT_3)):
					# Acquisition rate
					if self.timer.is_tick():
						# Acquire
						if self.acquire_sample():
							# Print
							trace_log(path, "SENSOR   > Record")
							# Share data
							self.share_data.write(f"{self.output.channel1:.3f}" + "," + f"{self.output.channel2:.3f}" + "," + f"{self.output.channel3:.3f}")
							# Store data
							file = open(filename, "a+")
							file.write(f"{self.output.timestamp:.3f}" + "," + f"{self.output.channel1:.3f}" + "," + f"{self.output.channel2:.3f}" + "," + f"{self.output.channel3:.3f}" + "\n")
							file.close()
					# Wait
					else:
						time.sleep(0.1)
				# Surface step
				elif ((navigation == USEA_NAVIGATION_STATE_SUB_SURFACE)
				   or (navigation == USEA_NAVIGATION_STATE_BUOYANCY_INCREASE)
				   or (navigation == USEA_NAVIGATION_STATE_SURFACE_ACQUISITION)):
					# Print
					trace_log(path, "SENSOR   > Stop acquisition")
					# Stop recording
					self.step = USEA_SENSOR_STEP_SURFACE
					# Share step
					self.share_step.write(self.step)
				# Other
				else:
					# Print
					trace_log(path, "SENSOR   > Stop acquisition")
					# Stop recording
					self.step = USEA_SENSOR_STEP_IDLE
					# Share step
					self.share_step.write(self.step)

			# Surface
			elif self.step == USEA_SENSOR_STEP_SURFACE:
				# Treatment step
				if navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Print
					trace_log(path, "SENSOR   > Start processing")
					# Start processing
					self.step = USEA_SENSOR_STEP_TREAT
					# Share step
					self.share_step.write(self.step)
					# Treatment
					time.sleep(15.0)
					# Print
					trace_log(path, "SENSOR   > Stop processing")
					# Stop processing
					self.step = USEA_SENSOR_STEP_IDLE
					# Share step
					self.share_step.write(self.step)
				# Surface step
				elif ((navigation == USEA_NAVIGATION_STATE_SUB_SURFACE)
				   or (navigation == USEA_NAVIGATION_STATE_BUOYANCY_INCREASE)
				   or (navigation == USEA_NAVIGATION_STATE_SURFACE_ACQUISITION)):
					# Ignore
					time.sleep(0.1)
				# Other
				else:
					# Stop recording
					self.step = USEA_SENSOR_STEP_IDLE
					# Share step
					self.share_step.write(self.step)

			# Other
			else:
				time.sleep(0.1)

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log(path, "SENSOR   > [ERROR]")


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
	sensor = DriverSensor()
	# Run
	sensor.run()

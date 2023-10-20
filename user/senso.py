#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	senso.py
	"""

# Standard libraries
import sys
import zipfile

# Project libraries
from system.io_lib import *
from system.serial_lib import *
from system.timer_lib import *
from system.share_lib import *

# Versioning
SENSO_VERSION = "v1.0.0"


# Acquisition process
def acquisition_process(self, string: str) -> bool:
	"""
		Sample acquisition process

		Returns:
			- bool: True if the acquisition process is successful
		"""
	# Print
	trace_log(path, "SENSO    > " + string)
	# Power-on
	self.io_power.set_on()
	# Warm-up
	time.sleep(3.5)
	# Acquisition
	frame_data = self.serial.receive_ascii(3.0)
	# Treatment
	if "SENSO,D," in frame_data[0:8]:
		# Parse
		split = frame_data.split(",")
		# Print
		trace_log(path, "SENSO    > Rx=" + frame_data)
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
		trace_log(path, "SENSO    > Time-out")
		# Result
		result = False
	# Power-off
	self.io_power.set_off()
	# Delay before new power-on (for proper operation of the sensor)
	time.sleep(0.5)
	# Result
	return result


# Output definition
class DataSenso:
	"""
		DataSenso class: sensor sample

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
class DriverSenso:
	"""
		DriverSenso class
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.active = False
		self.step = USEA_PAYLOAD_STEP_IDLE
		self.io_power = DriverIOOutput("CMDV2_4")
		self.io_alarm = DriverIOInput("ALARMS_4")
		self.serial = DriverSerial("COM5", 19200, 128, 0.15)
		self.timer = DriverTimer(path, "senso")
		self.share_data = FileShare(path, "senso.txt")
		self.share_step = DataShare("senso_step")
		# Output
		self.output = DataSenso()
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
			result = 3600.0
		elif self.step == USEA_PAYLOAD_STEP_IDLE:
			result = 3600.0
		elif self.step == USEA_PAYLOAD_STEP_RECORD:
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
class TestSenso:
	"""
		TestSenso class
		"""

	# Create resource
	def __init__(self):
		# Manager
		self.io_power = DriverIOOutput("CMDV2_4")
		self.serial = DriverSerial("COM5", 19200, 128, 0.15)
		# Output
		self.output = DataSenso()
		self.output.timestamp = 0.0
		self.output.channel1 = 0.0
		self.output.channel2 = 0.0
		self.output.channel3 = 0.0

	# Sensor version
	@staticmethod
	def get_version() -> str:
		"""
			Get version

			Returns:
				- str: version string
			"""
		return SENSO_VERSION

	# Test sensor
	def test(self) -> str:
		"""
			Test process

			Returns:
				- str: result string
			"""
		# Acquire
		if acquisition_process(self, "Test"):
			# Reply
			return "c1=" + f"{self.output.channel1:.3f}" +\
				", c2=" + f"{self.output.channel2:.3f}" +\
				", c3=" + f"{self.output.channel3:.3f}"
		# Error
		else:
			# Reply
			return "no reply"


# Compression
def compress():
	"""
		Compress the data files
		"""
	# Create names
	zip_src_name = path + "payload/"
	zip_tmp_name = path + "temp/" + get_profile(path) + "_payload.zip"
	zip_dst_name = path + "payload/" + get_profile(path) + "_payload.zip"
	# No file to compress
	if not os.listdir(zip_src_name):
		return
	# Remove src archive
	if os.path.isfile(zip_tmp_name):
		os.remove(zip_tmp_name)
	# Remove dst archive
	if os.path.isfile(zip_dst_name):
		os.remove(zip_dst_name)
	# Create archive
	zip_file = zipfile.ZipFile(zip_tmp_name, "w")
	# For files in folder
	while True:
		# Scan directory
		if not os.listdir(zip_src_name):
			break
		# File name
		file_name = os.listdir(zip_src_name)[0]
		# Add file
		zip_file.write(zip_src_name + file_name, file_name, compress_type=zipfile.ZIP_DEFLATED)
		# Remove file
		os.remove(zip_src_name + file_name)
	# Close archive
	zip_file.close()
	# Move archive
	os.rename(zip_tmp_name, zip_dst_name)


# Create resources
path = "./"
senso_driver = DriverSenso()


# Manager
def manager(self):
	global path
	file_name = ""

	# Trace
	trace_log(path, "SENSO    > Activate")

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
			if self.step == USEA_PAYLOAD_STEP_IDLE:
				# Ascent step
				if (
					(navigation == USEA_NAVIGATION_STATE_ASCENT) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_1) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_2) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_3)):
					# Create file name
					file_name = path + "payload/" + get_profile(path) + "_payload.csv"
					# Print
					trace_log(path, "SENSO    > Start acquisition")
					# Start recording
					self.step = USEA_PAYLOAD_STEP_RECORD
					# Share step
					self.share_step.write(self.step)
				# Wait
				else:
					time.sleep(0.1)

			# Record
			elif self.step == USEA_PAYLOAD_STEP_RECORD:
				# Ascent step
				if (
					(navigation == USEA_NAVIGATION_STATE_ASCENT) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_1) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_2) or
					(navigation == USEA_NAVIGATION_STATE_ASCENT_3)):
					# Acquisition rate
					if self.timer.is_tick():
						# Acquire
						if self.acquire_sample():
							# Print
							trace_log(path, "SENSO    > Record")
							# Share data
							self.share_data.write(
								f"{self.output.channel1:.3f}" + "," +
								f"{self.output.channel2:.3f}" + "," +
								f"{self.output.channel3:.3f}")
							# Store data
							file = open(file_name, "a+")
							file.write(
								f"{self.output.timestamp:.3f}" + "," +
								f"{self.output.channel1:.3f}" + "," +
								f"{self.output.channel2:.3f}" + "," +
								f"{self.output.channel3:.3f}" + "\n")
							file.close()
					# Wait
					else:
						time.sleep(0.1)
				# Surface step
				elif (
					(navigation == USEA_NAVIGATION_STATE_SUB_SURFACE) or
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_INCREASE) or
					(navigation == USEA_NAVIGATION_STATE_SURFACE_ACQUISITION)):
					# Print
					trace_log(path, "SENSO    > Stop acquisition")
					# Stop recording
					self.step = USEA_PAYLOAD_STEP_SURFACE
					# Share step
					self.share_step.write(self.step)
				# Other
				else:
					# Print
					trace_log(path, "SENSO    > Stop acquisition")
					# Stop recording
					self.step = USEA_PAYLOAD_STEP_IDLE
					# Share step
					self.share_step.write(self.step)

			# Surface
			elif self.step == USEA_PAYLOAD_STEP_SURFACE:
				# Treatment step
				if navigation == USEA_NAVIGATION_STATE_DATA_PROCESSING:
					# Print
					trace_log(path, "SENSO    > Start processing")
					# Start processing
					self.step = USEA_PAYLOAD_STEP_TREAT
					# Share step
					self.share_step.write(self.step)
					# Simulate treatment delay
					time.sleep(15.0)
					# Compress
					compress()
					# Print
					trace_log(path, "SENSO    > Stop processing")
					# Stop processing
					self.step = USEA_PAYLOAD_STEP_IDLE
					# Share step
					self.share_step.write(self.step)
				# Surface step
				elif (
					(navigation == USEA_NAVIGATION_STATE_SUB_SURFACE) or
					(navigation == USEA_NAVIGATION_STATE_BUOYANCY_INCREASE) or
					(navigation == USEA_NAVIGATION_STATE_SURFACE_ACQUISITION)):
					# Ignore
					time.sleep(0.1)
				# Other
				else:
					# Stop recording
					self.step = USEA_PAYLOAD_STEP_IDLE
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
		trace_log(path, "SENSO    > [ERROR]")


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
	senso = DriverSenso()
	# Run
	senso.run()

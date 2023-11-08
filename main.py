#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	main.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2023-11-08"
__version__ = "1.0.0"

# Standard libraries
import os
import time
import threading
import traceback

# Project libraries
from system.system import system_driver
from system.rtc import rtc_driver
from system.io_lib import DriverIOOutput
from system.technical import technical_driver
from system.ctd import ctd_driver
from system.emap import emap_driver
from system.config import user_driver
from system.trace_lib import trace_log


# Main function
if __name__ == "__main__":

	# Trace
	trace_log("./", "MAIN     > Launch application")

	# Restore system clock
	rtc_driver.restore()
	# CPLD awake command
	io_sleepn = DriverIOOutput("GPIO_3_27")
	io_sleepn.set_on()

	# Create paths
	if not os.path.exists("config"):
		os.makedirs("config")
	if not os.path.exists("share"):
		os.makedirs("share")
	if not os.path.exists("ctd"):
		os.makedirs("ctd")
	if not os.path.exists("payload"):
		os.makedirs("payload")
	if not os.path.exists("temp"):
		os.makedirs("temp")
	if not os.path.exists("log"):
		os.makedirs("log")
	if not os.path.exists("trash"):
		os.makedirs("trash")

	# Create tasks
	thread_technical = threading.Thread(target=technical_driver.run, name="task_technical")
	thread_ctd = threading.Thread(target=ctd_driver.run, name="task_ctd")
	thread_user = threading.Thread(target=user_driver.run, name="task_user")
	thread_emap = threading.Thread(target=emap_driver.run, name="task_emap")

	# Launch tasks
	thread_technical.start()
	thread_ctd.start()
	thread_user.start()
	thread_emap.start()

	# Main loop
	try:
		while True:

			# Wait
			time.sleep(1.0)

			# Activity management
			activity_emap = emap_driver.get_time_before_activity()
			activity_user = user_driver.get_time_before_activity()
			print("\t" + f"{activity_emap:.3f}" + "\t" + f"{activity_user:.3f}")

			# CPU power management
			if (activity_emap >= 300.0) and (activity_user >= 300.0):
				# Suspend system
				rtc_driver.program_wakealarm("5 minutes")
				# Trace
				trace_log("./", "MAIN     > Suspend system")
				# Suspend
				system_driver.suspend()

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log("./", "MAIN     > [ERROR]")

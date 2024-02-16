#!/bin/python
# -*- coding: utf-8 -*-
"""
	main.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-02-16"
__version__ = "1.0.0"

# Standard libraries
import os
import time
import threading
import traceback

# Project libraries
from system.system_lib import system_driver
from system.rtc import rtc_driver
from system.io_lib import DriverIOOutput
from system.technical import technical_driver
from system.web_server import web_server
from system.ctd import ctd_driver
from system.emap import emap_driver
from system.config import user_driver
from system.trace_lib import trace_log


# Main function
if __name__ == "__main__":

	# Validate booting process
	system_driver.boot_ok()
	# Feed the watchdog
	system_driver.watchdog_feed()

	# Create paths
	if not os.path.exists("log"):
		os.makedirs("log")
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
	if not os.path.exists("trash"):
		os.makedirs("trash")

	# Restore system clock
	rtc_driver.restore()
	# CPLD awake command
	io_sleepn = DriverIOOutput("GPIO_3_27")

	# Trace
	trace_log("MAIN     > Launch tasks")

	# Create tasks
	thread_technical = threading.Thread(target=technical_driver.run, name="task_technical", daemon=True)
	thread_web_server = threading.Thread(target=web_server.run, name="task_web_server", daemon=True)
	thread_emap = threading.Thread(target=emap_driver.run, name="task_emap", daemon=True)
	thread_ctd = threading.Thread(target=ctd_driver.run, name="task_ctd", daemon=True)
	thread_user = threading.Thread(target=user_driver.run, name="task_user", daemon=True)

	# Launch tasks
	thread_technical.start()
	thread_web_server.start()
	thread_emap.start()
	thread_ctd.start()
	thread_user.start()

	# Trace
	trace_log("MAIN     > Application is running")

	# Main loop
	try:
		while True:

			# Feed the watchdog
			system_driver.watchdog_feed()

			# Power management
			if os.path.isfile("share/sleep.txt"):
				# Tasks activity survey
				activity_emap = emap_driver.get_time_before_activity()
				activity_user = user_driver.get_time_before_activity()
				activity_next = int(min(activity_emap, activity_user))
				# No planned activity
				if activity_next >= 15:
					# Suspend CPLD
					io_sleepn.set_off()
					# Suspend system
					rtc_driver.program_wakealarm(activity_next - 5)
					# Awake CPLD
					io_sleepn.set_on()
				else:
					# Wait
					time.sleep(1.0)
			else:
				# Wait
				time.sleep(1.0)

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log("MAIN     > [ERROR]")

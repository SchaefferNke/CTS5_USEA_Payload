#!/bin/python
# -*- coding: utf-8 -*-
"""
	main.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-02-13"
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
#from system.web_socket import web_socket
from system.ctd import ctd_driver
from system.emap import emap_driver
from system.config import user_driver
from system.trace_lib import trace_log


# Main function
if __name__ == "__main__":

	# Validate booting process
	system_driver.boot_ok()

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

	# Trace
	trace_log("MAIN     > Launch application")

	# Restore system clock
	rtc_driver.restore()
	# CPLD awake command
	io_sleepn = DriverIOOutput("GPIO_3_27")

	# Create tasks
	thread_technical = threading.Thread(target=technical_driver.run, name="task_technical", daemon=True)
	thread_web_server = threading.Thread(target=web_server.run, name="task_web_server", daemon=True)
	#thread_web_socket = threading.Thread(target=web_socket.run, name="task_web_socket", daemon=True)
	thread_ctd = threading.Thread(target=ctd_driver.run, name="task_ctd", daemon=True)
	thread_emap = threading.Thread(target=emap_driver.run, name="task_emap", daemon=True)
	thread_user = threading.Thread(target=user_driver.run, name="task_user", daemon=True)

	# Launch tasks
	thread_technical.start()
	thread_web_server.start()
	#thread_web_socket.start()
	thread_ctd.start()
	thread_emap.start()
	thread_user.start()

	# Trace
	trace_log("MAIN     > Application loop")

	# Main loop
	try:
		while True:

			# Wait
			time.sleep(1.0)

			# Watchdog
			system_driver.watchdog_feed()

			# Activity management
			"""activity_emap = emap_driver.get_time_before_activity()
			activity_user = user_driver.get_time_before_activity()
			print("\t" + f"{activity_emap:.3f}" + "\t" + f"{activity_user:.3f}")

			# CPU power management
			if (activity_emap >= 300.0) and (activity_user >= 300.0):
				# Trace
				trace_log("MAIN     > Suspend system")
				# Suspend system
				rtc_driver.program_wakealarm("300")
				#system_driver.suspend()"""

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log("MAIN     > [ERROR]")

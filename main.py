#!/bin/python
# -*- coding: utf-8 -*-
"""
	main.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-09-30"
__version__ = "1.0.3"

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
from system.config import user_drivers
from system.trace_lib import trace_log

# Main function
if __name__ == "__main__":

	# Validate booting process
	system_driver.boot_ok()
	# Feed the watchdog
	system_driver.watchdog_feed()

	# Create paths
	for path in ("log", "config", "share", "ctd", "payload", "temp", "trash"):
		os.makedirs(path, exist_ok=True)

	# Cleanup files
	if os.path.exists("share/synchro.txt"):
		os.remove("share/synchro.txt")

	# Restore system clock
	rtc_driver.restore()
	# CPLD activation
	io_sleepn = DriverIOOutput("GPIO_3_27")
	io_sleepn.set_on()

	# Trace
	trace_log("MAIN     > Launch tasks")

	# Create system tasks
	thread_technical = threading.Thread(target=technical_driver.run, name="task_technical", daemon=True)
	thread_web_server = threading.Thread(target=web_server.run, name="task_web_server", daemon=True)
	thread_emap = threading.Thread(target=emap_driver.run, name="task_emap", daemon=True)
	thread_ctd = threading.Thread(target=ctd_driver.run, name="task_ctd", daemon=True)
	# Create user tasks
	user_threads = []
	for i, user in enumerate(user_drivers, 1):
		user_threads.append(threading.Thread(target=user.run, name=f"task_user{i}", daemon=True))

	# Launch system tasks
	thread_technical.start()
	thread_web_server.start()
	thread_emap.start()
	thread_ctd.start()
	# Launch user tasks
	for thread in user_threads:
		thread.start()

	# Trace
	trace_log("MAIN     > Application is running")

	# Main loop
	try:
		while True:

			# Feed the watchdog
			system_driver.watchdog_feed()

			# Power management
			if os.path.exists("share/sleep.txt"):
				# Tasks activity survey
				activities = [emap_driver.get_time_before_activity()]
				for driver in user_drivers:
					activities.append(driver.get_time_before_activity())
				activity_next = max(0, int(min(activities)))
				# No planned activity
				if activity_next > 20:
					# Suspend CPLD
					io_sleepn.set_off()
					# Suspend system
					rtc_driver.program_wakealarm_sleep(activity_next - 5)
					# Refresh EMAP heartbeat after wakeup
					emap_driver.heartbeat = time.monotonic()
					# Awake CPLD
					io_sleepn.set_on()
					# Wait
					time.sleep(5.0)
				else:
					# Wait
					time.sleep(1.0)
			else:
				# Wait
				time.sleep(1.0)

			# EMAP alive ?
			if time.monotonic() - emap_driver.heartbeat > 120:
				# Trace
				trace_log("MAIN     > EMAP blocked")
				# Clean folder
				files = os.listdir("./share")
				for file_name in files:
					os.remove("./share/" + file_name)
				# Reboot
				system_driver.reboot()

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log("MAIN     > [ERROR]")

	# Stop
	finally:
		# CPLD deactivation
		io_sleepn.set_off()

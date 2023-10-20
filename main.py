#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	main.py
	"""

# Standard libraries
import os
import time
import threading
import traceback

# Project libraries
from system.io_lib import *
from system.technical import technical_driver
from system.ctd import ctd_driver
from system.emap import emap_driver
from user.senso import senso_driver
from user.silicate import silicate_driver
from system.trace_lib import *

# Main function
if __name__ == "__main__":
	"""
		Application main function
		"""

	# Trace
	trace_log("./", "MAIN     > Launch application")

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

	# Create tasks
	thread_technical = threading.Thread(target=technical_driver.run, name="task_technical")
	thread_emap = threading.Thread(target=emap_driver.run, name="task_emap")
	thread_ctd = threading.Thread(target=ctd_driver.run, name="task_ctd")
	thread_senso = threading.Thread(target=senso_driver.run, name="task_senso")
	thread_silicate = threading.Thread(target=silicate_driver.run, name="task_silicate")

	# Launch tasks
	thread_technical.start()
	thread_emap.start()
	thread_ctd.start()
	thread_senso.start()
	thread_silicate.start()

	# CPLD activity
	io_sleepn = DriverIOOutput("SLEEPN_V2")

	# Main loop
	try:
		while True:

			# Activity management
			"""activity_emap = emap_driver.time_before_activity()
			activity_senso = senso_driver.time_before_activity()
			print("\t"+f"{activity_emap:+.3f}"+"\t"+f"{activity_senso:+.3f}")
			time.sleep(0.450)"""

			# CPLD activity
			io_sleepn.set_on()

	# Error
	except Exception as err:
		# Trace
		print(err)
		print(traceback.format_exc())
		# Trace
		trace_log(".", "MAIN     > [ERROR]")

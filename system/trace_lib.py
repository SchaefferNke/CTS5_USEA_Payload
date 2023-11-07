#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	trace_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2023-11-06"
__version__ = "1.0.0"

# Standard libraries
import datetime


# Print event
def trace_log(trace_path: str, event: str):
	"""
		Print on console and save event in logger file

		Parameters:
			- trace_path (str): ...
			- event (str): event to trace
	"""
	# Format
	utc = datetime.datetime.now()
	string = utc.strftime("%y-%m-%d %H:%M:%S : ") + event
	# Print to terminal
	print(string)
	# Save in logger
	log = open(trace_path + "log/payload.log", "a+")
	log.write(string + "\r")
	log.close()

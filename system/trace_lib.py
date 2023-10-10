#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
	trace_lib.py
	"""

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
	string = utc.strftime("%y-%m-%d %H:%M:%S ") + event
	# Print to terminal
	print(string)
	# Save in logger
	log = open(trace_path + "log/trace.log", "a+")
	log.write(string + "\r")
	log.close()

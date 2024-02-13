#!/bin/python
# -*- coding: utf-8 -*-
"""
	trace_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-02-13"
__version__ = "1.0.0"

# Standard libraries
import datetime


# Print event
def trace_log(event: str):
	"""
		Print on console and save event in logger file

		Parameters:
			- event (str): event to trace
	"""
	# Format
	utc = datetime.datetime.now()
	string = utc.strftime("%y-%m-%d %H:%M:%S : ") + event
	# Print to console
	print(string)
	# web_server include makes circular dependency
	from system.web_server import web_server
	# Send to websocket
	web_server.send(event)
	# Save in logger
	log = open("log/payload.log", "a+")
	log.write(string + "\r")
	log.close()

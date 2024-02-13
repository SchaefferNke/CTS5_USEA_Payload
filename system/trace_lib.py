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

# Project libraries
#from system.web_socket import web_socket


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
	# Send to websocket
	#web_socket.send(event)
	# Save in logger
	log = open("log/payload.log", "a+")
	log.write(string + "\r")
	log.close()

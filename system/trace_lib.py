#!/bin/python
# -*- coding: utf-8 -*-
"""
	trace_lib.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2026-02-11"
__version__ = "1.0.1"

# Standard libraries
import os
import datetime
import threading

# Constants
LOG_FILE = "log/payload.log"
LOG_MAX_SIZE = 5 * 1024 * 1024
LOG_MAX_FILES = 5

# Lock
_trace_lock = threading.Lock()
# Web server
web_server = None


# Get external web server
def set_web_server(ws):
	global web_server
	web_server = ws


# Manage multiple log files
def _rotate_log_if_needed():
	try:
		if not os.path.exists(LOG_FILE):
			return
		if os.path.getsize(LOG_FILE) < LOG_MAX_SIZE:
			return
		oldest = f"{LOG_FILE}.{LOG_MAX_FILES}"
		if os.path.exists(oldest):
			os.remove(oldest)
		for i in range(LOG_MAX_FILES - 1, 0, -1):
			src = f"{LOG_FILE}.{i}"
			dst = f"{LOG_FILE}.{i + 1}"
			if os.path.exists(src):
				os.rename(src, dst)
		os.rename(LOG_FILE, f"{LOG_FILE}.1")
	except (OSError, IOError):
		pass


# Print event
def trace_log(event: str):
	"""
		Print on console and save event in logger file

		Parameters:
			- event (str): event to trace
	"""
	# Format
	now = datetime.datetime.now()
	ds = now.microsecond // 100_000
	string = f"{now:%y-%m-%d %H:%M:%S}.{ds} : {event}"
	# Multi-thread protection
	with _trace_lock:
		# Print to console
		try:
			print(string, flush=True)
		except (OSError, ValueError):
			pass
		# Show in Web interface
		if web_server is not None:
			try:
				web_server.send(event)
			except (OSError, ConnectionError, AttributeError):
				pass
		# Save in logger
		try:
			_rotate_log_if_needed()
			with open(LOG_FILE, "a+", encoding="utf-8") as log:
				log.write(string + "\n")
		except (OSError, IOError):
			pass

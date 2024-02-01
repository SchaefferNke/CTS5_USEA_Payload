#!/bin/python
# -*- coding: utf-8 -*-
"""
	web_server.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-02-01"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import subprocess
import json
import logging

from flask import Flask, render_template, send_file, request

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.technical import technical_driver
from system.trace_lib import trace_log

# Web server
templateFolder = os.path.join(os.path.dirname(__file__), "web")
app = Flask(__name__, template_folder=templateFolder)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


# Get Flash python web framework
def get_app():
	global app
	return app


# Reboot query
@app.route("/reboot", methods=["POST"])
def reboot_post():
	# Trace
	trace_log("WEB      > Reboot")
	# TODO form = request.form
	# TODO subprocess.call(["reboot"])
	return "", 204


# Json query
@app.route("/payload.json", methods=["GET"])
def payload_get():
	return json.dumps(technical_driver.diagnosis_json(), indent=4)


# Web page
@app.route("/", defaults={"req_path": ""})
@app.route("/<path:req_path>")
def index(req_path):
	abs_path = os.path.join(templateFolder, req_path)
	if os.path.isfile(abs_path):
		return send_file(abs_path)
	return render_template("index.html")


# Class definition
class WebServer:
	"""
		WebServer class: manage web server
	"""

	# Create resource
	def __init__(self):
		# Server
		self._server = get_app()

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Trace
		trace_log("WEB      > Activate")
		# Start
		self._server.run(debug=False, use_reloader=False, host="0.0.0.0", port=8080)


# Create resources
web_server = WebServer()


# Test function
if __name__ == "__main__":
	# Run
	web_server.run()

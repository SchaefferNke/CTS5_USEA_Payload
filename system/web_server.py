#!/bin/python
# -*- coding: utf-8 -*-
"""
	web_server.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-01-31"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import json

from flask import Flask, render_template, send_file
from threading import Thread

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


# Get Flash python web framework
def get_app():
	global app
	return app


@app.route("/payload.json", methods=["GET"])
# Json query
def payload_get():
	return json.dumps(technical_driver.diagnosis_json(), indent=4)


@app.route("/", defaults={"req_path": ""})
@app.route("/<path:req_path>")
# Web page
def index(req_path):
	abs_path = os.path.join(templateFolder, req_path)
	if os.path.isfile(abs_path):
		return send_file(abs_path)
	return render_template("index.html")


class WebServer(Thread):
	"""
		WebServer class: manage web server
	"""

	# Create resource
	def __init__(self):
		# Server
		Thread.__init__(self, daemon=True, name="WebServer")
		self._server = get_app()

	# Run task
	def run(self):
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

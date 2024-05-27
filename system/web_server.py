#!/bin/python
# -*- coding: utf-8 -*-
"""
	web_server.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-05-27"
__version__ = "1.0.0"

# Standard libraries
import os
import sys
import time
import subprocess
import json
import logging

from flask import Flask, render_template, send_file
from flask_sock import Sock

if __name__ == "__main__":
	# Process launched outside main
	sys.path.insert(1, os.getcwd())
	sys.path.insert(1, "../")

# Project libraries
from system.technical import technical_driver
from system.emap import emap_driver
from system.trace_lib import trace_log

# Web server
templateFolder = os.path.join(os.path.dirname(__file__), "web")
app = Flask(__name__, template_folder=templateFolder)
app_sock = Sock(app)
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)


# Get Flash python web framework
def get_app():
	global app
	return app


# Reboot command
@app.route("/reboot", methods=["POST"])
def reboot_post():
	# Trace
	trace_log("WEB      > Reboot board")
	# Reboot
	if not os.name == "nt":
		subprocess.call(["sudo", "reboot"])
	# Reply
	return "", 204


# Restart command
@app.route("/restart", methods=["POST"])
def restart_post():
	# Trace
	trace_log("WEB      > Restart application")
	# Reboot
	if not os.name == "nt":
		os._exit(0)
	# Reply
	return "", 204


# Exit command
@app.route("/exit", methods=["POST"])
def exit_post():
	# Trace
	trace_log("WEB      > Exit application")
	# Reboot
	if not os.name == "nt":
		os._exit(1)
	# Reply
	return "", 204


# Sleep-on command
@app.route("/sleep-on.req", methods=["POST"])
def sleep_on_post():
	# Trace
	trace_log("WEB      > Sleep enabled")
	# Save
	if not os.path.isfile("share/sleep.txt"):
		file_request = open("share/sleep.txt", "w")
		file_request.close()
	# Reply
	return "", 204


# Sleep-off command
@app.route("/sleep-off.req", methods=["POST"])
def sleep_off_post():
	# Trace
	trace_log("WEB      > Sleep disabled")
	# Save
	if os.path.isfile("share/sleep.txt"):
		os.remove("share/sleep.txt")
	# Reply
	return "", 204


# Technical request
@app.route("/technical.json", methods=["GET"])
def technical_get():
	# Reply
	return json.dumps(technical_driver.status_json(), indent=1)


# EMAP request
@app.route("/emap.json", methods=["GET"])
def emap_get():
	# Reply
	return json.dumps(emap_driver.status_json(), indent=1)


# Page query
@app.route("/", defaults={"req_path": ""})
@app.route("/<path:req_path>")
def web_page(req_path):
	# Request
	abs_path = os.path.join(templateFolder, req_path)
	# Reply
	if os.path.isfile(abs_path):
		return send_file(abs_path)
	return render_template("index.html")


# Socket query
@app_sock.route('/rtlog')
def web_socket(wsock):
	while True:
		if web_server.message_rcv > web_server.message_trs + 1 and web_server.message_trs > 0:
			wsock.send("WEB      > ...")
		if web_server.message_rcv > web_server.message_trs:
			wsock.send(web_server.message_str)
			web_server.message_trs = web_server.message_rcv
		time.sleep(0.01)


# Class definition
class WebServer:
	"""
		WebServer class: manage web server
	"""

	# Create resource
	def __init__(self):
		# Server
		self._server = get_app()
		# Message
		self.message_trs = 0
		self.message_rcv = 0
		self.message_str = ""

	# Send message
	def send(self, message: str):
		"""
			Send message

			Parameters:
				- message (str): message to send
		"""
		# Increment message
		self.message_rcv += 1
		# Store message
		self.message_str = message

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

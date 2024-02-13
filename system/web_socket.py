#!/bin/python
# -*- coding: utf-8 -*-
"""
	web_socket.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-02-13"
__version__ = "1.0.0"

# Standard libraries
import os
import time
#import asyncio
#import websockets

from flask import Flask
from flask_sock import Sock

# Web server
templateFolder = os.path.join(os.path.dirname(__file__), "sock")
app = Flask(__name__, template_folder=templateFolder)
app_sock = Sock(app)


# Get Flash python web framework
def get_app():
	global app
	return app


@app_sock.route('/rtlog')
def nm(sock):
	while True:
		if web_socket.message_rcv > web_socket.message_trs + 1 and web_socket.message_trs > 0:
			sock.send("WSOCK > ...")
		if web_socket.message_rcv > web_socket.message_trs:
			sock.send(web_socket.message_str)
			web_socket.message_trs = web_socket.message_rcv
		time.sleep(0.1)


# Class definition
class WebSocket:
	"""
		WebSocket class: manage websocket
	"""

	"""async def handler(self, websocket):
		while True:
			if self._message_rcv > self._message_trs + 1 and self._message_trs > 0:
				await websocket.send("...")
			if self._message_rcv > self._message_trs:
				await websocket.send(self._message_str)
				self._message_trs = self._message_rcv
			await asyncio.sleep(0.01)"""

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
				- message (str): String to send
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
		# Start
		self._server.run(debug=False, use_reloader=False, host="0.0.0.0", port=3856)
		# Start
		"""loop = asyncio.new_event_loop()
		#asyncio.set_event_loop(loop)
		#server = websockets.serve(self.handler, host="0.0.0.0", port=50000)
		#asyncio.get_event_loop().run_until_complete(server)
		#asyncio.get_event_loop().run_forever()"""


# Create resources
web_socket = WebSocket()

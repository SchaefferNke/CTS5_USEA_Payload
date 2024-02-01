#!/bin/python
# -*- coding: utf-8 -*-
"""
	web_socket.py
"""

__authors__ = "Christophe SCHAEFFER"
__copyright__ = "nke Instrumentation"
__date__ = "2024-02-01"
__version__ = "1.0.0"

# Standard libraries
import asyncio
import websockets


# Class definition
class WebSocket:
	"""
		WebSocket class: manage websocket
	"""

	async def handler(self, websocket):
		while True:
			if self._message_rcv > self._message_trs + 1 and self._message_trs > 0:
				await websocket.send("...")
			if self._message_rcv > self._message_trs:
				await websocket.send(self._message_str)
				self._message_trs = self._message_rcv
			await asyncio.sleep(0.01)

	# Create resource
	def __init__(self):
		# Server
		self._message_trs = 0
		self._message_rcv = 0
		self._message_str = ""

	# Send message
	def send(self, message: str):
		"""
			Send message

			Parameters:
				- message (str): String to send
		"""
		# Increment message
		self._message_rcv += 1
		# Store message
		self._message_str = message

	# Run task
	def run(self):
		"""
			Working task
		"""
		# Start
		loop = asyncio.new_event_loop()
		asyncio.set_event_loop(loop)
		server = websockets.serve(self.handler, host="0.0.0.0", port=5678)
		asyncio.get_event_loop().run_until_complete(server)
		asyncio.get_event_loop().run_forever()


# Create resources
web_socket = WebSocket()

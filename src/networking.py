#!/usr/bin/env python

import struct
import time
from socket import *

UDP_IP = "<broadcast>"
UDP_PORT = 31337 


def monitor_base_time():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT))

	while True:
        	data, addr = sock.recvfrom(100)
		base_time = struct.unpack('!Q',data)
		print base_time
		time.sleep(1)


def broadcast_base_time(base_time):
	sock = socket(AF_INET, SOCK_DGRAM)
	sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
	sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

	while True:
		msg = struct.pack("!Q", base_time)
		sock.sendto(msg, ('10.0.10.255', UDP_PORT))
		time.sleep(1)
	

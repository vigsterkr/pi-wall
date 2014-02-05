#!/usr/bin/env python

import sys
from player import Player
from gi.repository import GObject
from networking import *

if __name__ == "__main__":
	loop = GObject.MainLoop()
	player = Player()
	player.play("file:///home/pi/Park_720p.mp4")
	player.loop = True
	base_time = player.set_master(11111)
	broadcast_base_time(base_time)
	try:
		loop.run()
	except KeyboardInterrupt:
		sys.exit(1)


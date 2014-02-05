#!/usr/bin/env python

import sys
from player import Player
from gi.repository import GObject

if __name__ == "__main__":
	loop = GObject.MainLoop()
	player = Player()
	player.play("file:///home/pi/Park_720p.mp4")
	player.loop = True
	
	try:
		loop.run()
	except KeyboardInterrupt:
		sys.exit(1)


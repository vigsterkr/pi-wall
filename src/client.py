#!/usr/bin/env python

import sys
from player import * 
from gi.repository import GObject

if __name__ == "__main__":
	slave = SlaveThread(sys.argv[1], sys.argv[2])
	slave.start()
	
	try:
		GObject.MainLoop.run()
	except KeyboardInterrupt:
		slave.stop_player()
		sys.exit(1)


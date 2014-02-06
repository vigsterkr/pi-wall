#!/usr/bin/env python

import sys
from player import * 
from gi.repository import GObject
from networking import *

if __name__ == "__main__":
	player = MasterPlayer(sys.argv[1], int(sys.argv[2]))
	ms = MasterServerThread(player, sys.argv[3])
	ms.start()

	try:
		GObject.MainLoop().run()
	except KeyboardInterrupt:
		ms.stop()
		sys.exit(1)


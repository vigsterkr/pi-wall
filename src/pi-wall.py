#!/usr/bin/env python

import sys
from player import * 
from gi.repository import GObject
from networking import *
import json

if __name__ == "__main__":
	try:
		f = open('/etc/pi-wall.conf')
	except IOError:
		print "cannot open config file"
	else:
		config = json.load(f)
		f.close()
	
		if config['type'] == 'master':
			player = MasterPlayer(config['movie_file'], int(config['master_port']))
			ms = MasterServerThread(player, config['bcast_addr'])
			ms.start()

			try:
				GObject.MainLoop().run()
			except KeyboardInterrupt:
				ms.stop()
				sys.exit(1)
		elif config['type'] == 'slave':
			slave = SlaveThread(config['movie_file'], config['bcast_addr'])
			slave.start()

			try:
				GObject.MainLoop().run()
			except KeyboardInterrupt:
				slave.stop_player()
				sys.exit(1)
		else:
			print "error type"



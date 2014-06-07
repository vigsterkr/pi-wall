#!/usr/bin/env python

import sys
from player import *
from gi.repository import GObject
from networking import *
import json

if __name__ == "__main__":
    try:
        config_file = '/etc/pi-wall.conf'
        if len(sys.argv) == 2:
            config_file = sys.argv[1]
        f = open(config_file)
    except IOError:
        print "cannot open config file"
    else:
        config = json.load(f)
        f.close()

        GObject.threads_init()
        loop = GObject.MainLoop()
        if config['type'] == 'master':
            player = MasterPlayer(config['movie_file'],
                                  int(config['master_port']))
            ms = MasterServerThread(player)
            ms.start()

            try:
                loop.run()
            except KeyboardInterrupt:
                ms.stop()
                sys.exit(1)
        elif config['type'] == 'slave':
            slave = SlaveThread(config['movie_file'])
            slave.start()

            try:
                loop.run()
            except KeyboardInterrupt:
                slave.stop()
                sys.exit(1)
        else:
            print "error type"

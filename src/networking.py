#!/usr/bin/env python

import struct
import time
from socket import *
import threading
from player import *

UDP_PORT = 31337


class MasterServerThread(threading.Thread):
    def __init__(self, master_player, bcast_addr):
        super(MasterServerThread, self).__init__()
        self.master_player = master_player
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        self.bcast_addr = bcast_addr
        self.running = True

    def run(self):
        while self.running:
            msg = struct.pack("!Qi", self.master_player.base_time,
                              self.master_player.port)
            self.sock.sendto(msg, (self.bcast_addr, UDP_PORT))
            time.sleep(1)

    def stop(self):
        self.master_player.stop()
        self.running = False


class SlaveThread(threading.Thread):
    def __init__(self, filepath, bcast_addr):
        super(SlaveThread, self).__init__()
        self.filepath = filepath
        self.slave = None
        self.running = True
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind((bcast_addr, UDP_PORT))

    def run(self):
        while self.running:
            data, addr = self.sock.recvfrom(100)
            base_time, port = struct.unpack('!Qi', data)
            ip = addr[0]
#           print base_time, ip, port

            if self.slave is None:
                self.slave = SlavePlayer(self.filepath, ip, port, base_time)
            elif base_time != self.slave.base_time:
                print("base time does not match, restarting...")
                self.slave.stop()
                self.slave = SlavePlayer(self.filepath, ip, port, base_time)

    def stop_player(self):
        self.slave.stop()
        self.running = False

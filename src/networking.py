#!/usr/bin/env python

import time
import threading
from player import *
import pybonjour
import select
import zmq

regtype = '_pi-wall._tcp'


def DNSServiceRef_hash(self):
    """
    make pybonjour.DNSServiceRef hashable, i.e. zmq.Poller compatible
    """
    return hash(self.fileno())
pybonjour.DNSServiceRef.__hash__ = DNSServiceRef_hash


class MasterServerThread(threading.Thread):
    def __init__(self, master_player):
        super(MasterServerThread, self).__init__()
        self.master_player = master_player
        self.watch_id = self.master_player.connect("finished",
                                                   self.on_finished)
        self.running = False
        self.sdref = pybonjour.DNSServiceRegister(name='pi-wall',
                                                  regtype=regtype,
                                                  port=self.master_player.port)
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind("tcp://*:%d" % self.master_player.port)

    def send_update(self):
        pdu = {'base-time': self.master_player.base_time}
        self.socket.send_json(pdu)

    def on_finished(self, player):
        """
        Player finished playing content, when looping base time needs update
        """
        if player.loop:
            self.send_update()

    def run(self):
        self.master_player.play()
        self.running = True
        while self.running:
            self.send_update()
            time.sleep(1)

    def stop(self):
        self.master_player.stop()
        self.running = False

        self.sdref.close()
        self.master_player.disconnect(self.watch_id)
        self.socket.close()
        self.context.term()


class SlaveThread(threading.Thread):
    def __init__(self, filepath):
        super(SlaveThread, self).__init__()
        self.filepath = filepath
        self.slave_player = None
        self.running = False
        self.sd_ref = pybonjour.DNSServiceBrowse(regtype=regtype,
                                                 callBack=self.browse_callback)
        self.timeout = 5
        self.resolved = []
        self.context = zmq.Context()
        self.subscriber = None

    def get_ip(self, hosttarget, port):
        ips = pybonjour.socket.getaddrinfo(hosttarget, port, 0,
                                           pybonjour.socket.SOCK_DGRAM, 0)

        ipv4 = [item for item in ips if item[0] == pybonjour.socket.AF_INET]
        ipv6 = [item for item in ips if item[0] == pybonjour.socket.AF_INET6]
        if len(ipv4):
            return ipv4[0][4][0]
        elif len(ipv6):
            return ipv6[0][4][0]

        return None

    def subscribe(self, ip, port):
        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect("tcp://%s:%d" % (ip, port))
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b'')
        self.poller.register(self.subscriber, zmq.POLLIN)

    def unsubscribe(self):
        if self.subscriber is not None:
            self.poller.unregister(self.subscriber)
            self.subscriber.close()
            self.subscriber = None

    def start_player(self, ip, port, base_time):
        if self.slave_player is None:
            self.slave_player = SlavePlayer(self.filepath, ip, port, base_time)
            self.slave_player.play()
        elif base_time != self.slave_player.base_time:
            self.slave_player.stop()
            self.slave_player.update_base_time(base_time)
            self.slave_player.play()

    def resolve_callback(self, sdRef, flags, interfaceIndex, errorCode,
                         fullname, hosttarget, port, txtRecord):
        if errorCode == pybonjour.kDNSServiceErr_NoError:
            ip = self.get_ip(hosttarget, port)
            self.subscribe(ip, port)
            pdu = self.subscriber.recv_json()
            self.start_player(ip, port, int(pdu['base-time']))

            self.resolved.append(True)

    def browse_callback(self, sdRef, flags, interfaceIndex, errorCode,
                        serviceName, regtype, replyDomain):
        if errorCode != pybonjour.kDNSServiceErr_NoError:
            return

        if not (flags & pybonjour.kDNSServiceFlagsAdd):
            self.unsubscribe()
            return

        resolve_sdRef = pybonjour.DNSServiceResolve(0,
                                                    interfaceIndex,
                                                    serviceName,
                                                    regtype,
                                                    replyDomain,
                                                    self.resolve_callback)
        try:
            while not self.resolved:
                ready = select.select([resolve_sdRef], [], [], self.timeout)
                if resolve_sdRef not in ready[0]:
                    print 'Resolve timed out'
                    break
                pybonjour.DNSServiceProcessResult(resolve_sdRef)
            else:
                self.resolved.pop()
        finally:
            resolve_sdRef.close()

    def run(self):
        self.running = True
        self.poller = zmq.Poller()
        self.poller.register(self.sd_ref, zmq.POLLIN)
        while self.running:
            socks = dict(self.poller.poll())
            if self.sd_ref.fileno() in socks and socks[self.sd_ref.fileno()] == zmq.POLLIN:
                pybonjour.DNSServiceProcessResult(self.sd_ref)

            if self.subscriber in socks and socks[self.subscriber] == zmq.POLLIN:
                pdu = self.subscriber.recv_json()
                current_base_time = int(pdu['base-time'])
                if current_base_time != self.slave_player.base_time:
                    self.slave_player.stop()
                    self.slave_player.update_base_time(current_base_time)
                    self.slave_player.play()

    def stop(self):
        if self.slave_player is not None:
            self.slave_player.stop()
        self.running = False

        self.unsubscribe()
        self.context.term()
        self.sd_ref.close()

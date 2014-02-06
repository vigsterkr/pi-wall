#!/usr/bin/python

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GstNet, GObject

GObject.threads_init()
Gst.init(None)

class Player(object):
	def __init__(self, filepath):
		self._filepath = filepath
		self.player = self.get_pipeline()

		self.bus = self.player.get_bus()
		self.bus.add_signal_watch()
	        self.bus.connect("message", self.on_bus_msg)
		
		self._loop = False
		
		self.player.set_state(Gst.State.PAUSED)
		
		# bug ? as i get -1 for the standard
		self.GST_CLOCK_TIME_NONE = 18446744073709551615

		self._prerolling = True

	
	def stop(self):
		self.player.set_state(Gst.State.NULL)

	
	def get_pipeline(self):
		return Gst.parse_launch('filesrc location={0} ! '.format(self._filepath) + 'decodebin ! autovideosink')


	def on_bus_msg(self, bus, msg):
		if msg is None:
			return
		elif msg.type is Gst.MessageType.SEGMENT_DONE: 
			self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.SEGMENT, 0)
		elif msg.type is Gst.MessageType.ASYNC_DONE:
			if self._prerolling:
				self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.SEGMENT, 0)
				self.player.set_state(Gst.State.PLAYING)
				self._prerolling = False
		elif msg.type is Gst.MessageType.ERROR:
			print "Got message of type ", msg.type
			print "Got message of src ", msg.src
			print "Got message of error ", msg.parse_error()
			self.player.set_state(Gst.State.NULL)


	def about_to_finish(self, playbin):
		print "about to finish"
		if self._loop:
			print "adding to loop"
	                self.player.props.uri = self._last_uri


	@property	
	def loop(self):
		return self._loop 


	@loop.setter
	def loop(self, value):
		self._loop = value


class MasterPlayer(Player):
	def __init__(self, filepath, port):
		super(MasterPlayer, self).__init__(filepath)
		
		self._port = port
		self._clock = self.player.get_clock()
		self.player.use_clock(self._clock)
		self._clock_provider = GstNet.NetTimeProvider.new(self._clock, None, self._port)
		self._base_time = self._clock.get_time()
		self.player.set_start_time(self.GST_CLOCK_TIME_NONE)
		self.player.set_base_time(self._base_time)

	@property
	def base_time(self):
		return self._base_time


	@property
	def port(self):
		return self._port


class SlavePlayer(Player):
	def __init__(self, filepath, ip, port, base_time):
		super(SlavePlayer, self).__init__(filepath)
		self._ip = ip
        	self._port = port
        	self._base_time = base_time

	
	@property
	def base_time(self):
		return self._base_time


	@base_time.setter
	def base_time(self, value):
		self.player.set_start_time(self.GST_CLOCK_TIME_NONE)
                self._base_time = value
                self._clock = GstNet.NetClientClock.new("clock", self._ip, self._port, self._base_time)
                self.player.set_base_time(self._base_time)
                self.player.use_clock(self._clock)


if __name__ == '__main__':
	import sys
	print sys.argv[1]

	if sys.argv[1] == 'master':
		player = MasterPlayer(sys.argv[2], 11111)
		print("base_time={0}".format(player.base_time))
	elif sys.argv[1] == 'slave':
		player = SlavePlayer(sys.argv[2], sys.argv[3], 11111, int(sys.argv[4]))
		player.base_time = int(sys.argv[4])
	else:
		player = Player(sys.argv[1])

	GObject.MainLoop().run()


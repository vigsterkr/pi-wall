#!/usr/bin/python

from gi.repository import Gst
from gi.repository import GstNet

class Player(object):
	def __init__(self):
		Gst.init (None)
		self.player = Gst.ElementFactory.make("playbin", "Player")

		self.bus = self.player.get_bus()
		self.bus.add_signal_watch()
	        self.bus.connect("message", self.on_bus_msg)
       		self.player.connect("about-to-finish", self.about_to_finish)
		self._loop = False
		
		# bug ? as i get -1 for the standard
		self.GST_CLOCK_TIME_NONE = 18446744073709551615

		self._slave = False
		self._master = False

	
	def play(self, uri):
		self._last_uri = uri
		self.player.props.uri = self._last_uri
		self.player.set_state (Gst.State.PLAYING)


	def on_bus_msg(self, bus, msg):
		if msg is None:
			return
		elif msg.type is Gst.MessageType.ERROR:
			print "Got message of type ", msg.type
			print "Got message of src ", msg.src
			print "Got message of error ", msg.parse_error()
			self.player.set_state(Gst.State.NULL)

 
	def about_to_finish(self, playbin):
		if self._loop:
			print "adding to loop"
			self.player.props.uri = self._last_uri 


	@property	
	def loop(self):
		return self._loop 


	@loop.setter
	def loop(self, value):
		self._loop = value


	@property
	def slave(self):
		return self._slave


	def set_slave(self, ip, port, base_time):
		self.player.set_start_time(self.GST_CLOCK_TIME_NONE)
		self._clock = GstNet.NetClientClock.new("clock", ip, port, base_time)
		self.player.set_base_time(base_time)
		self.player.use_clock(self._clock)

		self._slave = True


	def set_master(self, port):
	    	self._clock = self.player.get_clock()
    		self.player.use_clock(self._clock)

    		self._clock_provider = GstNet.NetTimeProvider.new(self._clock, None, port)

    		base_time = self._clock.get_time()

    		self.player.set_start_time(self.GST_CLOCK_TIME_NONE)
    		self.player.set_base_time(base_time)
		
		self._master = True
		
		return base_time

	


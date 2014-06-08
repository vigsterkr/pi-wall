#!/usr/bin/python

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GstNet, GObject
import platform

Gst.init(None)


class Player(GObject.GObject):
    __gsignals__ = {
        'finished': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    def __init__(self, filepath):
        GObject.GObject.__init__(self)

        self._filepath = filepath
        self.loop = True

        # create pipeline
        self.pipeline = Gst.Pipeline()
        self.playbin = Gst.ElementFactory.make('playbin', None)
        self.pipeline.add(self.playbin)
        self.playbin.set_property('uri', 'file://{0}'.format(self._filepath))

        # create & add sinks
        if platform.system() == 'Darwin':
            audio_sink = Gst.ElementFactory.make('osxaudiosink', None)
            video_sink = Gst.ElementFactory.make('osxvideosink', None)
        elif platform.system() == 'Linux':
            audio_sink = Gst.ElementFactory.make('alsasink', None)
            video_sink = Gst.ElementFactory.make('eglglessink', None)

        audio_sink.set_property('sync', True)
        video_sink.set_property('sync', True)
        self.playbin.set_property('audio-sink', audio_sink)
        self.playbin.set_property('video-sink', video_sink)

        self.bus = self.pipeline.get_bus()
        self.watch_id = self.bus.connect("message", self.on_bus_msg)
        self.bus.add_signal_watch()

        self.pipeline.set_state(Gst.State.PAUSED)

        # bug ? as i get -1 for the standard
        self.GST_CLOCK_TIME_NONE = 18446744073709551615

    def release(self):
        self.pipeline.remove(self.playbin)
        del self.playbin
        self.bus.remove_signal_watch()
        self.bus.disconnect(self.watch_id)
        del self.pipeline
        del self.bus

    def play(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)

    def on_bus_msg(self, bus, msg):
        if msg is None:
            return
        elif msg.type is Gst.MessageType.EOS:
            if self.loop:
                self.playbin.seek_simple(Gst.Format.TIME,
                                         Gst.SeekFlags.FLUSH
                                         | Gst.SeekFlags.KEY_UNIT, 0)
                self.base_time = self.pipeline.get_clock().get_time()
                self.pipeline.set_base_time(self.base_time)
            self.emit('finished')

        elif msg.type is Gst.MessageType.ERROR:
            print "Got message of type ", msg.type
            print "Got message of src ", msg.src
            print "Got message of error ", msg.parse_error()
            self.pipeline.set_state(Gst.State.NULL)

    @property
    def content(self):
        return self._filepath

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value):
        self._loop = value

    @property
    def base_time(self):
        return self._base_time

    @base_time.setter
    def base_time(self, value):
        self._base_time = value


class MasterPlayer(Player):
    def __init__(self, filepath, port):
        super(MasterPlayer, self).__init__(filepath)

        self._port = port
        clock = self.pipeline.get_clock()
        self.pipeline.use_clock(clock)
        self._clock_provider = GstNet.NetTimeProvider.new(clock,
                                                          None,
                                                          self._port)
        self.base_time = clock.get_time()
        self.pipeline.set_start_time(self.GST_CLOCK_TIME_NONE)
        self.pipeline.set_base_time(self.base_time)

    def release(self):
        del self._clock_provider
        super(MasterPlayer, self).release()

    @property
    def port(self):
        return self._port


class SlavePlayer(Player):
    def __init__(self, filepath, ip, port, base_time):
        super(SlavePlayer, self).__init__(filepath)
        self._ip = ip
        self._port = port
        self.base_time = base_time
        self.pipeline.set_start_time(self.GST_CLOCK_TIME_NONE)
        self._clock = GstNet.NetClientClock.new("clock",
                                                self._ip,
                                                self._port,
                                                self._base_time)
        self.pipeline.set_base_time(self.base_time)
        self.pipeline.use_clock(self._clock)
        self.loop = False

    def update_base_time(self, base_time):
        self.base_time = base_time
        self.pipeline.set_base_time(self.base_time)

if __name__ == '__main__':
    import sys

    if sys.argv[1] == 'master':
        player = MasterPlayer(sys.argv[2], 11111)
        print("base_time={0}".format(player.base_time))
    elif sys.argv[1] == 'slave':
        player = SlavePlayer(sys.argv[2], sys.argv[3], 11111, int(sys.argv[4]))
    else:
        player = Player(sys.argv[1])

    player.play()

    GObject.MainLoop().run()

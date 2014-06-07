#A basic video wall for Raspberry Pi

This set of scripts helps you to create a synchronized video wall with the help of a farm of Raspberry PIs.

It is based on ```gstreamer 1.0``` since it's using ```gstreamer1.0-omx``` for decoding the video content

## Install
I had a lot of troubles with getting this to work on Raspberry PI, as there are some bugs in some of the firmwares and gstreamer versions and distributions. Hence here's a known to work setup:

### Requirements
   * [Raspbian](http://downloads.raspberrypi.org/raspbian_latest) distro
   * Make sure that your firmware is ```Linux fox3 3.10.25+ #624 PREEMPT``` as some of the newer ones seems to have some sort of bug. Hence run:

    ```
sudo rpi-update b42b4d8a038b2d3f13c3c7b4dc9e9cb9307b78ed
    ```
   * Install the ```gstreamer 1.0``` packages from ```http://vontaene.de/raspbian-updates```:

   ```
sudo echo "deb http://vontaene.de/raspbian-updates/ . main" > /etc/apt/sources.list.d/gstreamer.list
sudo apt-get update
sudo apt-get install gstreamer1.0-alsa gstreamer1.0-plugins-good \
gstreamer1.0-plugins-bad gstreamer1.0-omx gstreamer1.0-tools \
gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0
    ```

### Configuration
  After you have the required packages installed on all the PIs.

#### config variables
  * ```type```: ```master``` or ```slave```
  * ```bcast_addr```: the [broadcast address](http://en.wikipedia.org/wiki/Broadcast_address#IP_networking) on which the PIs can communicate to each other.
  * ```movie_file```: full path to the audio-video content you want to play on the given PI.
  * ```master_port```: the port on which the ```master``` binds ```GstNetTimeProvider``` i.e. the reference clock for the ```slaves```.

  The ```pi-wall.conf``` files should be placed under ```/etc/```:
  ```
  sudo cp config/pi-wall.conf.master_example /etc/pi-wall.conf
  ```

#### running
Once all the ```config``` files are set and copied to the right place. simply execute the ```pi-wall.py``` script on all of the PIs:
```
./src/pi-wall.py
```

After couple of seconds the movies will start to play in sync! ENJOY!

#### auto-starting
In order to start the movies automatically even after the PIs are rebooted (power-failure etc.), simply used the provided ```init.d``` script:
```
sudo cp scripts/pi-wall /etc/init.d/
sudo update-rc.d pi-wall defaults
```

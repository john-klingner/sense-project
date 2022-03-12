# sense-project

## Long-term Goal

Have `N` Feather Sense boards all reporting environmental sensor data to the cloud.

## Current Status

Uses Adafruit's Broadcastnet library to have an RPi4 hub bridge between the Feather Sense boards and Adafruit IO. Basically just trying to implement [this tutorial](https://learn.adafruit.com/bluetooth-le-broadcastnet-sensor-node-raspberry-pi-wifi-bridge/broadcastnet-on-aio).
   - Feather Sense runs `code.py`.
   - RPi4 runs `rpi_hub.py`.

This works out-of-the-box, except that after 5-10 minutes python crashes with an 
```
OSError: [Errno 24] Too many open files
```
when trying to start a scan. Scanning is apparently done with file objects under the hood, and there's some memory leak type issue whereby the file objects aren't properly cleaned up when scanning is done.
To get things working long-term, the fix is apparently to put the `hicitool.off` file in this repo (named `hcitool`) somewhere in your PATH before `/usr/bin/hcitool` (e.g, in `~/bin/hcitool`. The `hcitool.off` file just returns an error, which causes the bluetooth library to switch to some sort of backup utility instead of hcitool, which doesn't have this memory leak issue.

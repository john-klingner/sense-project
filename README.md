# sense-project

## Long-term Goal

Have `N` Feather Sense boards all reporting environmental sensor data to the cloud.


## Current Status

There are two approaches in here:
1. Uses a bluetooth-as-UART connection to transmit/receive sensor readings between Feather Sense boards. For this,
   - One Feather Sense runs `uart_sense_receiver_code.py`.
   - A second Feather Sense runs `uart_sense_transmitter_code.py`.
   - Both boards need `uart_sensor_packet.py`.
   
   This works, but I don't think will scale to support multiple sensors all transmitting to one central hub.
2. Uses Adafruit's Broadcastnet library to have an RPi4 hub bridge between the Feather Sense boards and Adafruit IO. Basically just trying to implement [this tutorial](https://learn.adafruit.com/bluetooth-le-broadcastnet-sensor-node-raspberry-pi-wifi-bridge/broadcastnet-on-aio).
   - Feather Sense runs `broadcastnet_sense_code.py`.
   - RPi4 runs `broadcastnet_rpi_code.py`.
   
   This is not working for me. I think my next step should be to re-install everything on my RPi4 in case I inadvertently messed with my bluetooth drivers while trying to get things working earlier.

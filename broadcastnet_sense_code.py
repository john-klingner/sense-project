# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This is a complex sensor node that uses the sensors 
   on a Clue and Feather Bluefruit Sense."""

import time

import adafruit_ble_broadcastnet
from sensors import Sensors
import name

def ToSensorMeasurement(sensors):
    measurement = adafruit_ble_broadcastnet.AdafruitSensorMeasurement()
    measurement.temperature = sensors.getTemperature()
    measurement.relative_humidity = sensors.getHumidity()
    measurement.pressure = sensors.getBaroPressure()
    measurement.acceleration = sensors.getAccel()
    measurement.magnetic = sensors.getMagnetic()
    measurement.gyro = sensors.getGyro()
    # Using 'value' for board id
    measurement.value = name.kBoardId
    return measurement
    
print("This is BroadcastNet sensor:", adafruit_ble_broadcastnet.device_address)
sensors = Sensors()

while True:
    measurement = ToSensorMeasurement(sensors)
    print(measurement)
    adafruit_ble_broadcastnet.broadcast(measurement)
    time.sleep(4)

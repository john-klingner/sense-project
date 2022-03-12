# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This is a complex sensor node that uses the sensors
   on a Clue and Feather Bluefruit Sense."""

import time

from sensors import Sensors
import name
import adafruit_ble_broadcastnet


def ToSensorMeasurement(sensors):
    measurement = adafruit_ble_broadcastnet.AdafruitSensorMeasurement()
    measurement.temperature = sensors.getTemperature()
    measurement.pressure = sensors.getBaroPressure()
    measurement.relative_humidity = sensors.getHumidityShort()
    return measurement


print("This is BroadcastNet sensor:", adafruit_ble_broadcastnet.device_address)
sensors = Sensors()

while True:
    measurement = ToSensorMeasurement(sensors)
    print(measurement)
    adafruit_ble_broadcastnet.broadcast(measurement)
    time.sleep(10)

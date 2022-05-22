# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT
"""This is a complex sensor node that uses the sensors
   on a Clue and Feather Bluefruit Sense."""

import time

from aio_interface import WifiIoMqttConnection
from sensors import Sensors
import _bleio


def CollectMeasurements(sensors):
    return {
        #Convert temperature to fahrenheit.
        "temperature": 32.0 + (1.8 * sensors.getTemperature()),
        "pressure": sensors.getBaroPressure(),
        "relative-humidity": sensors.getHumidityShort(),
        "loudness": sensors.getLoudness(),
    }


kMyIdByte = _bleio.adapter.address.address_bytes[0]
kMyId = "{:02x}".format(kMyIdByte)
kMyGroupKey = "sensor-" + kMyId

print("This is BroadcastNet sensor:", kMyId)
sensors = Sensors()
connection = WifiIoMqttConnection()
while True:
    measurement = CollectMeasurements(sensors)
    print(measurement)
    connection.Publish(kMyGroupKey, measurement)
    time.sleep(10)

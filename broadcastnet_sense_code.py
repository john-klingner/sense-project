# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This is a complex sensor node that uses the sensors 
   on a Clue and Feather Bluefruit Sense."""

import time

import sensor_measurement
from sensors import Sensors
import name

def ToSensorMeasurement(sensors):
    measurement = sensor_measurement.SensorMeasurement()
    measurement.temperature = sensors.getTemperature()
    measurement.pressure = sensors.getBaroPressure()
    measurement.relative_humidity =sensors.getHumidityShort()
    measurement.color = sensors.getColors()
    measurement.boardId = name.kBoardId
    return measurement
    
print("This is BroadcastNet sensor:", sensor_measurement.device_address)
sensors = Sensors()

while True:
    measurement = ToSensorMeasurement(sensors)
    print(measurement)
    sensor_measurement.broadcast(measurement)
    time.sleep(4)

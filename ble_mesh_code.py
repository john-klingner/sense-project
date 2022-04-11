# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This is a complex sensor node that uses the sensors
   on a Clue and Feather Bluefruit Sense."""

import time

from sensors import Sensors
import adafruit_ble_broadcastnet
from adafruit_ble_broadcastnet import _ble as ble

def ToSensorMeasurement(sensors):
    measurement = adafruit_ble_broadcastnet.AdafruitSensorMeasurement()
    measurement.temperature = sensors.getTemperature()
    measurement.pressure = sensors.getBaroPressure()
    measurement.relative_humidity = sensors.getHumidityShort()
    return measurement

def GetIdByte(measurement):
    if measurement.address is None:
        return 0xFF
    return measurement.address.address_bytes[0]

def ToId(id_byte):
    return "{:02x}".format(id_byte)

def GetId(measurement):
    return ToId(GetIdByte(measurement))

_last_seen_sequence_numbers = {}
_measurements = []
_sequence_number = 0
_sensors = Sensors()
_last_broadcast = 0
_my_id_byte = ble._adapter.address.address_bytes[0]

def HandleMeasurement(measurement):
    global _last_seen_sequence_numbers
    original_source_id = GetId(measurement)
    if (original_source_id not in _last_seen_sequence_numbers) or (_last_seen_sequence_numbers[original_source_id] != measurement.sequence_number):
        print("\tReceived {} from {}.".format(measurement, original_source_id))
        _measurements.append(measurement)
        _last_seen_sequence_numbers[original_source_id] = measurement.sequence_number


def HandleSending(measurement):
    ble.start_advertising(measurement, scan_response=None)
    time.sleep(0.5)
    ble.stop_advertising()

def HandleBroadcast():
    global _sequence_number
    global _my_id_byte
    my_measurement = ToSensorMeasurement(_sensors)
    my_measurement.sequence_number = _sequence_number
    print("Sending: {}".format(my_measurement))
    HandleSending(my_measurement)
    _last_seen_sequence_numbers[_my_id_byte] = _sequence_number
    _sequence_number = (_sequence_number + 1) % 256


print("This is BroadcastNet sensor: ", ToId(_my_id_byte))

while True:
    now = time.time()
    for received_measurement in ble.start_scan(
        adafruit_ble_broadcastnet.AdafruitSensorMeasurement, interval=0.1,timeout=1.0,minimum_rssi=-100
    ):
        HandleMeasurement(received_measurement)
    for received_measurement in _measurements:
        HandleSending(received_measurement)
    _measurements = []
    if(now - _last_broadcast) >= 15:
        HandleBroadcast()
        _last_broadcast = now
    time.sleep(0.01)

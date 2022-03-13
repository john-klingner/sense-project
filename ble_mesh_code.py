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
    reversed_address = [measurement.address.address_bytes[i]
                        for i in range(5, -1, -1)]
    sensor_address = "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(
        *reversed_address)
    return reversed_address[-1]
    
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
    global _last_seen_sequence_number
    source_id = GetId(measurement)
    original_source_id = ToId(measurement.value)
    print("Received from {} by way of {}:\n\t{}".format(original_source_id, source_id, measurement))
    if original_source_id not in _last_seen_sequence_numbers:
        _last_seen_sequence_numbers[original_source_id] = (measurement.sequence_number - 1) % 256
    if _last_seen_sequence_numbers[original_source_id] != measurement.sequence_number:
        _measurements.append(measurement)
        _last_seen_sequence_numbers[original_source_id] = measurement.sequence_number
    
    
def HandleSending(measurement):
    ble.start_advertising(measurement, scan_response=None)
    time.sleep(0.5)
    ble.stop_advertising()

def HandleBroadcast():
    global _sequence_number
    global _last_broadcast
    global _my_id_byte
    my_measurement = ToSensorMeasurement(_sensors)
    my_measurement.value = _my_id_byte
    my_measurement.sequence_number = _sequence_number
    print("Sending: {}".format(my_measurement))
    HandleSending(my_measurement)
    _sequence_number = (_sequence_number + 1) % 256
    _last_broadcast = now
    

print("This is BroadcastNet sensor: ", ToId(_my_id_byte))

while True:
    now = time.time()
    for received_measurement in ble.start_scan(
        adafruit_ble_broadcastnet.AdafruitSensorMeasurement, interval=0.5,timeout=10.0,minimum_rssi=-100
    ):
        HandleMeasurement(received_measurement)
    for received_measurement in _measurements:
        print("Forwarding: {}".format(received_measurement))
        HandleSending(received_measurement)
    _measurements = []
    if(now - _last_broadcast) >= 10:
        HandleBroadcast()
    time.sleep(0.01)

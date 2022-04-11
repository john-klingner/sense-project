# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This is a complex sensor node that uses the sensors
   on a Clue and Feather Bluefruit Sense."""

import time
import random

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

kSendDurationS = 0.5
kPeriodS = 15.0
_last_seen_sequence_numbers = {}
_sequence_number = 0
_sensors = Sensors()
_my_id_byte = ble._adapter.address.address_bytes[0]

def HandleSending(measurement):
    global kSendDurationS
    print("\tSending: {}".format(measurement))
    ble.start_advertising(measurement, scan_response=None)
    time.sleep(kSendDurationS)
    ble.stop_advertising()
    return None

def HandleMeasurement(measurement):
    global _last_seen_sequence_numbers
    original_source_id = GetId(measurement)
    if (original_source_id not in _last_seen_sequence_numbers) or (_last_seen_sequence_numbers[original_source_id] != measurement.sequence_number):
        now = time.monotonic()
        pre_forward_delay_s = random.uniform(0,(kPeriodS-kSendDurationS)/2)
        print("\t\tReceived {} from {} at {}, scheduling for {} in the future.".format(measurement, original_source_id, now, pre_forward_delay_s))
        _scheduled_sends.append((time.monotonic()+pre_forward_delay_s,lambda meas=measurement: HandleSending(meas)))
        _last_seen_sequence_numbers[original_source_id] = measurement.sequence_number

def HandleBroadcast():
    global _sequence_number
    global _scheduled_sends
    global _my_id_byte
    my_measurement = ToSensorMeasurement(_sensors)
    my_measurement.sequence_number = _sequence_number
    HandleSending(my_measurement)
    _last_seen_sequence_numbers[_my_id_byte] = _sequence_number
    _sequence_number = (_sequence_number + 1) % 256
    return (kPeriodS, HandleBroadcast)


print("This is BroadcastNet sensor: ", ToId(_my_id_byte))

_scheduled_sends = [(time.monotonic(), HandleBroadcast)]

while True:
    now = time.monotonic()
    for received_measurement in ble.start_scan(
        adafruit_ble_broadcastnet.AdafruitSensorMeasurement, interval=0.1,timeout=1.0,minimum_rssi=-100
    ):
        HandleMeasurement(received_measurement)
    time_to_send = [send for send in _scheduled_sends if (now >= send[0])]
    for (scheduled_time, fn) in time_to_send:
        print("\t\tCalling function scheduled for {} at {}.".format(scheduled_time, now))
        result = fn()
        if result is not None:
            new_send_time = scheduled_time + result[0]
            print("\t\tScheduling new send for {}.".format(new_send_time))
            _scheduled_sends.append((new_send_time,result[1]))
    _scheduled_sends = [send for send in _scheduled_sends if (now < send[0])]
    time.sleep(0.01)

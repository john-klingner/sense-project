# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This example bridges from BLE to Adafruit IO on a Raspberry Pi."""
from secrets import secrets  # pylint: disable=no-name-in-module
import time
import requests
from adafruit_ble.advertising.standard import ManufacturerDataField
from adafruit_ble.advertising import Advertisement
import adafruit_ble
import sensor_measurement

aio_auth_header = {"X-AIO-KEY": secrets["aio_key"]}
aio_base_url = "https://io.adafruit.com/api/v2/" + secrets["aio_username"]

def byte_string(s):
    return "".join("%02x" % b for b in s)


ble = adafruit_ble.BLERadio()
bridge_address = sensor_measurement.device_address
print("This is BroadcastNet bridge:", bridge_address)
print("scanning")
print()
sequence_numbers = {}
# By providing Advertisement as well we include everything, not just specific advertisements.
print(sensor_measurement.SensorMeasurement.match_prefixes)
while True:
    for measurement in ble.start_scan(
        Advertisement, interval=0.5
    ):
        print(byte_string(bytes(measurement)))
        reversed_address = [measurement.address.address_bytes[i] for i in range(5, -1, -1)]
        sensor_address = "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(*reversed_address)
        # Skip if we are getting the same broadcast more than once.
        group_key = "bridge-{}-sensor-{}".format(bridge_address, sensor_address)
        data = [group_key]
        for attribute in dir(measurement.__class__):
            attribute_instance = getattr(measurement.__class__, attribute)
            if issubclass(attribute_instance.__class__, ManufacturerDataField):
                    values = getattr(measurement, attribute)
                    if values is not None:
                        data.extend([values, attibute, attribute_instance])

        start_time = time.monotonic()
        print(data)
        # Only update the previous sequence if we logged successfully.

        duration = time.monotonic() - start_time
        print("Done logging measurement to IO. Took {} seconds".format(duration))
        print()

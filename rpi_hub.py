#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import logging
logging.basicConfig(format="[%(levelname)s] %(asctime)s: %(message)s",
                    level=logging.INFO)

"""This example bridges from BLE to Adafruit IO on a Raspberry Pi."""
import time
from adafruit_ble.advertising.standard import ManufacturerDataField
import adafruit_ble
import adafruit_ble_broadcastnet
from aio_interface import ConvertToFeedData, AIOInterface

def forfor(a):
    return [item for sublist in a for item in sublist]

def GetIdByte(measurement):
    if measurement.address is None:
        return 0xFF
    return measurement.address.address_bytes[0]

def ToId(id_byte):
    return "{:02x}".format(id_byte)

def GetId(measurement):
    return ToId(GetIdByte(measurement))

def FeedDatumFromAttribute(measurement, attribute):
    attribute_instance = getattr(measurement.__class__, attribute)
    if issubclass(attribute_instance.__class__, ManufacturerDataField):
        if (attribute == "sequence_number"):
            return None
        values = getattr(measurement, attribute)
        if values is not None:
            return ConvertToFeedData(values, attribute, attribute_instance)
    return None

ble = adafruit_ble.BLERadio()
bridge_address = adafruit_ble_broadcastnet.device_address
logging.info("This is BroadcastNet bridge:{}\n".format(bridge_address))

aio_interface = AIOInterface()

logging.info("Scanning\n")
sequence_numbers = {}
# By providing Advertisement as well we include everything, not just specific advertisements.
while True:
    logging.info("Starting Scan")
    for measurement in ble.start_scan(
        adafruit_ble_broadcastnet.AdafruitSensorMeasurement, minimum_rssi=-100
    ):
        sensor_id = GetId(measurement)
        logging.info("Received {} from {}.".format(measurement, sensor_id))
        # Check sequence numbers.
        if sensor_id not in sequence_numbers:
            logging.info("\tThis is a new sensor_id.")
            sequence_numbers[sensor_id] = measurement.sequence_number - 1 % 256
        # Skip if we are getting the same broadcast more than once.
        if measurement.sequence_number == sequence_numbers[sensor_id]:
            logging.warning("\tSkipping.")
            continue

        aio_interface.CreateGroupIfNeeded(sensor_id)

        # Pull data from measurement:
        data = forfor(list(filter(None, [FeedDatumFromAttribute(measurement, attribute) for attribute in dir(measurement.__class__)])))

        for feed_datum in data:
            aio_interface.CreateFeedIfNeeded(feed_datum["key"], sensor_id)

        # Log the data:
        start_time = time.monotonic()
        log_successful = aio_interface.LogData(data, sensor_id)
        duration = time.monotonic() - start_time

        if log_successful:
            sequence_numbers[sensor_id] = measurement.sequence_number
            logging.info("\tLogged measurement to IO. Took {} seconds.\n".format(duration))

#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""This example bridges from BLE to Adafruit IO on a Raspberry Pi."""
from secrets import secrets  # pylint: disable=no-name-in-module
import time
import requests
from adafruit_ble.advertising.standard import ManufacturerDataField
import adafruit_ble
import adafruit_ble_broadcastnet
import logging

logging.basicConfig(format="[%(levelname)s] %(asctime)s: %(message)s",
                    level=logging.INFO)

aio_auth_header = {"X-AIO-KEY": secrets["aio_key"]}
aio_base_url = "https://io.adafruit.com/api/v2/" + secrets["aio_username"]


def aio_post(path, **kwargs):
    kwargs["headers"] = aio_auth_header
    return requests.post(aio_base_url + path, **kwargs)


def aio_get(path, **kwargs):
    kwargs["headers"] = aio_auth_header
    return requests.get(aio_base_url + path, **kwargs)


# Disable outer names check because we frequently collide.
# pylint: disable=redefined-outer-name

def create_group(name):
    response = aio_post("/groups", json={"name": name})
    if response.status_code != 201:
        raise RuntimeError("unable to create new group with name {}\n{}\n{}".format(
            name, response.content, response.status_code))
    return response.json()["key"]


def create_feed(group_key, name):
    response = aio_post(
        "/groups/{}/feeds".format(group_key), json={"feed": {"name": name}}
    )
    if response.status_code != 201:
        raise RuntimeError("unable to create new feed named {} in group {}.\n{}\n{}".format(
            name, group_key, response.content, response.status_code))
    return response.json()["key"]


def create_data(group_key, data):
    response = aio_post("/groups/{}/data".format(group_key),
                        json={"feeds": data})
    if response.status_code == 429:
        logging.warning("Throttled!")
        return False
    if response.status_code != 200:
        raise RuntimeError("unable to create new data ({}) in group {}\n{}\n{}.".format(
            data, group_key, response.status_code, response.json()))
    response.close()
    return True


def convert_to_feed_data(values, attribute_name, attribute_instance):
    feed_data = []
    # Wrap single value entries for enumeration.
    if not isinstance(values, tuple) or (
        attribute_instance.element_count > 1 and not isinstance(
            values[0], tuple)
    ):
        values = (values,)
    for i, value in enumerate(values):
        key = attribute_name.replace("_", "-")
        if(len(values) > 1):
            key = key + "-" + str(i)
        if isinstance(value, tuple):
            for j in range(attribute_instance.element_count):
                feed_data.append(
                    {
                        "key": key + "-" + attribute_instance.field_names[j],
                        "value": value[j],
                    }
                )
        else:
            if key == "temperature":
                # Convert to fahrenheit.
                value = (value*1.8)+32.0
            feed_data.append({"key": key, "value": value})
    return feed_data


def GetId(measurement):
    reversed_address = [measurement.address.address_bytes[i]
                        for i in range(5, -1, -1)]
    sensor_address = "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(
        *reversed_address)
    return "{:02x}".format(reversed_address[-1])


ble = adafruit_ble.BLERadio()
bridge_address = adafruit_ble_broadcastnet.device_address
logging.info("This is BroadcastNet bridge:{}\n".format(bridge_address))

logging.info("Fetching existing feeds.")

existing_feeds = {}
response = aio_get("/groups")
for group in response.json():
    if "-" not in group["key"]:
        continue
    pieces = group["key"].split("-")
    if len(pieces) != 2 or pieces[0] != "sensor":
        continue
    _, sensor_id = pieces

    logging.info("Found feed with id: {}.".format(sensor_id))

    existing_feeds[sensor_id] = []
    for feed in group["feeds"]:
        feed_key = feed["key"].split(".")[-1]
        existing_feeds[sensor_id].append(feed_key)

logging.info("Existing Feeds:\n{}".format(existing_feeds))

logging.info("Scanning\n")
sequence_numbers = {}
# By providing Advertisement as well we include everything, not just specific advertisements.
while True:
    for measurement in ble.start_scan(
        adafruit_ble_broadcastnet.AdafruitSensorMeasurement, interval=0.5
    ):
        sensor_id = GetId(measurement)

        # Check sequence numbers.
        if sensor_id not in sequence_numbers:
            sequence_numbers[sensor_id] = measurement.sequence_number - 1 % 256
        # Skip if we are getting the same broadcast more than once.
        if measurement.sequence_number == sequence_numbers[sensor_id]:
            logging.warning("Skipping: {}".format(measurement))
            continue

        # Create Group if needed:
        group_key = "sensor-" + sensor_id
        if sensor_id not in existing_feeds:
            logging.info("Sensor id ({}) not in existing feeds: {}".format(
                sensor_id, existing_feeds))
            create_group("Sensor " + sensor_id)
            existing_feeds[sensor_id] = []

        # Pull data from measurement:
        data = []
        for attribute in dir(measurement.__class__):
            attribute_instance = getattr(measurement.__class__, attribute)
            if issubclass(attribute_instance.__class__, ManufacturerDataField):
                if (attribute == "sequence_number"):
                    continue
                values = getattr(measurement, attribute)
                if values is not None:
                    data.extend(
                        convert_to_feed_data(
                            values, attribute, attribute_instance)
                    )

        # Create feeds if needed:
        for feed_data in data:
            if feed_data["key"] not in existing_feeds[sensor_id]:
                create_feed(group_key, feed_data["key"])
                existing_feeds[sensor_id].append(feed_data["key"])

        start_time = time.monotonic()

        # Log the data:
        log_successful = create_data(group_key, data)

        if log_successful:
            sequence_numbers[sensor_id] = measurement.sequence_number

        duration = time.monotonic() - start_time
        logging.info(
            "Done logging measurement to IO. Took {} seconds.\n".format(duration))

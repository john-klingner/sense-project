from secrets import secrets  # pylint: disable=no-name-in-module
import time
import requests
import logging

aio_auth_header = {"X-AIO-KEY": secrets["aio_key"]}
aio_base_url = "https://io.adafruit.com/api/v2/" + secrets["aio_username"]

def to_group_key(sensor_id): return "sensor-" + sensor_id

def aio_post(path, **kwargs):
    kwargs["headers"] = aio_auth_header
    return requests.post(aio_base_url + path, **kwargs)

def aio_get(path, **kwargs):
    kwargs["headers"] = aio_auth_header
    return requests.get(aio_base_url + path, **kwargs)

def create_group(name):
    response = aio_post("/groups", json={"name": name})
    if response.status_code != 201:
        raise RuntimeError("unable to create new group with name {}\n{}\n{}".format(
            name, response.content, response.status_code))
    return response.json()["key"]


def create_feed(sensor_id, name):
    group_key = to_group_key(sensor_id)
    response = aio_post(
        "/groups/{}/feeds".format(group_key), json={"feed": {"name": name}}
    )
    if response.status_code != 201:
        raise RuntimeError("unable to create new feed named {} in group {}.\n{}\n{}".format(
            name, group_key, response.content, response.status_code))
    return response.json()["key"]

def ConvertToFeedData(values, attribute_name, attribute_instance):
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

class AIOInterface:
    existing_feeds = {}

    def __init__(self):
        logging.info("Fetching existing feeds.")
        response = aio_get("/groups")
        for group in response.json():
            if "-" not in group["key"]:
                continue
            pieces = group["key"].split("-")
            if len(pieces) != 2 or pieces[0] != "sensor":
                continue
            _, sensor_id = pieces

            logging.info("Found feed with id: {}.".format(sensor_id))

            self.existing_feeds[sensor_id] = []
            for feed in group["feeds"]:
                feed_key = feed["key"].split(".")[-1]
                self.existing_feeds[sensor_id].append(feed_key)

        logging.info("Existing Feeds:\n{}".format(self.existing_feeds))

    def CreateGroupIfNeeded(self, sensor_id):
        if sensor_id not in self.existing_feeds:
            logging.info("Sensor id ({}) not in existing feeds: {}".format(
                sensor_id, self.existing_feeds))
            create_group("Sensor " + sensor_id)
            self.existing_feeds[sensor_id] = []

    def CreateFeedIfNeeded(self, feed_key, sensor_id):
        if feed_key not in self.existing_feeds[sensor_id]:
            logging.info("{} feed not in eisting feeds for {}.".format(feed_key, sensor_id))
            create_feed(sensor_id, feed_key)
            self.existing_feeds[sensor_id].append(feed_key)


    def LogData(self, data, sensor_id):
        group_key = to_group_key(sensor_id)
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
import time
import board
import busio
from digitalio import DigitalInOut
import neopixel
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket

import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT
from adafruit_io.adafruit_io_errors import AdafruitIO_MQTTError

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise


# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print("Connected to MQTT broker!")
    # Subscribe to topics here.


def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from MQTT Broker!")


def message(client, topic, message):
    """Method callled when a client's subscribed feed has a new
    value.
    :param str topic: The topic of the feed with a new value.
    :param str message: The new value
    """
    print("New message on topic {0}: {1}".format(topic, message))


class WifiIoMqttConnection:

    def __init__(self):
        esp32_cs = DigitalInOut(board.D13)
        esp32_reset = DigitalInOut(board.D12)
        esp32_ready = DigitalInOut(board.D11)

        spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
        esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready,
                                               esp32_reset)

        status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.1)
        self.wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(
            esp, secrets, status_light)

        print("Connecting to WiFi...")
        self.wifi.connect()
        print("Connected!")
        time.sleep(0.1)

        # Initialize MQTT interface with the esp interface
        MQTT.set_socket(socket, esp)

        mqtt_client = MQTT.MQTT(
            broker="io.adafruit.com",
            username=secrets["aio_username"],
            password=secrets["aio_key"],
        )
        self.io = IO_MQTT(mqtt_client)

        self.io.on_connect = connected
        self.io.on_disconnect = disconnected
        self.io.on_message = message
        time.sleep(0.1)
        self.Connect()

    def Connect(self):
        try:
            self.io.connect()
            self.io.subscribe_to_throttling()
        except AdafruitIO_MQTTError as err:
            print("Failed to connect. Will retry.\n", err)

    def OnLoop(self):
        if self.io.is_connected():
            try:
                self.io.loop()
            except (ValueError, RuntimeError) as e:
                print("Failed to get data, retrying\n", e)
                self.Reset()
        else:
            print("Not connected. Trying to connect in loop.\n")
            self.Connect()

    def Publish(self, group, values):
        if not self.io.is_connected():
            print("IO Connection not established. Skipping publish call.")
            return
        for (feed_name, value) in values.items():
            try:
                self.io.publish('.'.join([group, feed_name]), value)
            except AdafruitIO_MQTTError as err:
                print("Failed to publish.\n", err)

    def Reset(self):
        self.wifi.reset()
        self.io.reconnect()

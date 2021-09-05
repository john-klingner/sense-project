# SPDX-FileCopyrightText: 2020 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Receives SensorPackets over the adafruit UARTService.
"""

import time

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_ble.services.standard.device_info import DeviceInfoService

from adafruit_bluefruit_connect.packet import Packet

from sensor_packet import SensorPacket


def byte_string(s):
    return "".join("%02x" % b for b in s)

ble = BLERadio()
uart = UARTService()
advertisement = ProvideServicesAdvertisement(uart)

print("Starting loop.")
while True:
    ble.start_advertising(advertisement)
    while not ble.connected:
        pass
    while ble.connected:
        try:
            packet = Packet.from_stream(uart)
        except ValueError as ve:
            in_bytes = uart.read(23)
            print(f"ValueError ({ve}).")
            print(byte_string(in_bytes))
            break
        if packet:
            if isinstance(packet, SensorPacket):
                print(f"{packet.board_id:02x} Sent: "
                    f"{packet.temperature:.2f} *C, "
                    f"{packet.pressure/100:.2f} HPa, "
                    f"{packet.humidity:.1f}%, "
                    f"Color: ({packet.r}, {packet.g}, {packet.b}, {packet.c})"
                )
            else:
                print(f"Not SensorPacket: {packet.to_bytes()}")
    ble.stop_advertising()


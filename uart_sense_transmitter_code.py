# SPDX-FileCopyrightText: 2020 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
Transmits SensorPackets over the adafruit UARTService.
"""

import time

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService
from adafruit_ble.services.standard.device_info import DeviceInfoService

from adafruit_bluefruit_connect.packet import Packet

from uart_sensor_packet import SensorPacket
from sensors import Sensors

import name


def byte_string(s):
    return "".join("%02x" % b for b in s)

def ToSensorPacket(sensors):
    return SensorPacket(name.kBoardId, sensors.getTemperature(),
                        sensors.getBaroPressure(), sensors.getHumidity(),
                        *sensors.getColors())

ble = BLERadio()

sensors = Sensors()

uart_connection = None
# See if any existing connections are providing UARTService.
if ble.connected:
    for connection in ble.connections:
        if UARTService in connection:
            uart_connection = connection
        break

while True:
    if not uart_connection:
        print("Scanning...")
        for adv in ble.start_scan(ProvideServicesAdvertisement, timeout=5):
            if UARTService in adv.services:
                print("found a UARTService advertisement")
                uart_connection = ble.connect(adv)
                break
        # Stop scanning whether or not we are connected.
        ble.stop_scan()

    while uart_connection and uart_connection.connected:
        packet = ToSensorPacket(sensors)
        print(
                f"Sending Packet from {packet.board_id:02x}: {packet.temperature:.2f} *C, "
                f"{packet.pressure/100:.2f} HPa, "
                f"{packet.humidity:.1f}%, "
                f"Color: ({packet.r}, {packet.g}, {packet.b}, {packet.c})"
            )
        try:
            uart_connection[UARTService].write(packet.to_bytes())
        except OSError as err:
            print(f"Connection lost ({err})")
            try:
                uart_connection.disconnect()
            except:  # pylint: disable=bare-except
                pass
            uart_connection = None
        time.sleep(1)




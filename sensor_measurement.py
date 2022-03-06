# Adapted from adafruit_ble_croadcastnet.py

import struct
import adafruit_ble
import os
import time

from micropython import const
from adafruit_ble.advertising import Advertisement, LazyObjectField
from adafruit_ble.advertising.standard import ManufacturerData, ManufacturerDataField

_ble = adafruit_ble.BLERadio()  # pylint: disable=invalid-name

def broadcast(measurement, *, broadcast_time=0.1):
    _ble.start_advertising(measurement, scan_response=None)
    time.sleep(broadcast_time)
    _ble.stop_advertising()

# This line causes issues with Sphinx, so we won't run it in the CI
if not hasattr(os, "environ") or (
    "GITHUB_ACTION" not in os.environ and "READTHEDOCS" not in os.environ
):
    if _ble._adapter.address:  # pylint: disable=protected-access
        device_address = "{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}".format(  # pylint: disable=invalid-name
            *reversed(
                list(
                    _ble._adapter.address.address_bytes  # pylint: disable=protected-access
                )
            )
        )
    else:
        device_address = "000000000000"  # pylint: disable=invalid-name
        """Device address as a string."""

_MANUFACTURING_DATA_ADT = const(0xFF)
_ADAFRUIT_COMPANY_ID = const(0x0822)
_SENSOR_MEASUREMENT_ID = const(0x0003)

class SensorMeasurement(Advertisement):
    """A collection of sensor measurements."""

    # This prefix matches all
    match_prefixes = (
        # Matches the sequence number field header (length+ID)
        struct.pack(
            "<BHBH", 
            _MANUFACTURING_DATA_ADT, 
            _ADAFRUIT_COMPANY_ID, 
            struct.calcsize("<HffHHHHHBH"), 
            _SENSOR_MEASUREMENT_ID
        ),
    )

    manufacturer_data = LazyObjectField(
        ManufacturerData,
        "manufacturer_data",
        advertising_data_type=_MANUFACTURING_DATA_ADT,
        company_id=_ADAFRUIT_COMPANY_ID,
        key_encoding="<H",
    )

    temperature = ManufacturerDataField(0x0A04, "<f")
    """Temperature as a float in degrees centigrade."""

    pressure = ManufacturerDataField(0x0A05, "<f")
    """Pressure as a float in hectopascals."""

    relative_humidity = ManufacturerDataField(0x0A06, "<H")
    """Relative humidity as a percentage in the interval [0,65535]."""    

    color = ManufacturerDataField(0x0A07, "<HHHH", ("r", "g", "b", "c"))
    """Color as RGBC quartet of unsigned shorts."""

    board_id = ManufacturerDataField(0x0A08, "<B")
    """Board ID as unsigned byte."""

    battery_voltage = ManufacturerDataField(0x0A0A, "<H")
    """Battery voltage in millivolts. Saves two bytes over voltage and is more readable in bare
       packets."""

    def __str__(self):
        parts = []
        for attr in dir(self.__class__):
            attribute_instance = getattr(self.__class__, attr)
            if issubclass(attribute_instance.__class__, ManufacturerDataField):
                value = getattr(self, attr)
                if value is not None:
                    parts.append("{}={}".format(attr, str(value)))
        return "<{} {} >".format(self.__class__.__name__, " ".join(parts))
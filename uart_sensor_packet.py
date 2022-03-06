import struct
from adafruit_bluefruit_connect.packet import Packet


class SensorPacket(Packet):
    """A packet containing environmental sensor readings."""

    _FMT_PARSE = "<xxBfffHHHHx"
    PACKET_LENGTH = struct.calcsize(_FMT_PARSE)
    # _FMT_CONSTRUCT doesn't include the trailing checksum byte.
    _FMT_CONSTRUCT = "<2sBfffHHHH"
    _TYPE_HEADER = b"!S"

    def __init__(
        self,
        board_id: int,
        temperature: float,
        pressure: float,
        humidity: float,
        r: int,
        g: int,
        b: int,
        c: int
    ):
        """TODO
        """
        self._board_id = board_id
        self._temperature = temperature
        self._pressure = pressure
        self._humidity = humidity
        self._r = r
        self._g = g
        self._b = b
        self._c = c
        

    def to_bytes(self):
        """Return the bytes needed to send this packet."""
        partial_packet = struct.pack(
            self._FMT_CONSTRUCT,
            self._TYPE_HEADER,
            self._board_id,
            self._temperature,
            self._pressure,
            self._humidity,
            self._r,
            self._g,
            self._b,
            self._c
        )
        return self.add_checksum(partial_packet)
    
    @property
    def board_id(self):
        """ uint8_t representing the source board's ID. """
        return self._board_id    

    @property
    def temperature(self):
        """ Float representing temperature in degrees Celsius. """
        return self._temperature

    @property
    def pressure(self):
        """ Float representing pressure in pascals. """
        return self._pressure

    @property
    def humidity(self):
        """ Float representing humidity as a percentage on [0,100]. """
        return self._humidity

    @property
    def r(self):
        """ uint16_t representing red intensity on [0,65535]. """
        return self._r

    @property
    def g(self):
        """ uint16_t representing gree intensity on [0,65535]. """
        return self._g

    @property
    def b(self):
        """ uint16_t representing blue intensity on [0,65535]. """
        return self._b

    @property
    def c(self):
        """ uint16_t representing 'clear' intensity on [0,65535]. """
        return self._c


# Register this class with the superclass. This allows the user to import only what is needed.
SensorPacket.register_packet_type()

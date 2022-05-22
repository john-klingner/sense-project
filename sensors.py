"""Sensor demo for Adafruit Feather Sense.
Prints data from each of the sensors."""
import array
import math

import board
import ulab
import ulab.numpy as np

import audiobusio
import adafruit_apds9960.apds9960
import adafruit_bmp280
import adafruit_lis3mdl
import adafruit_lsm6ds.lsm6ds33
import adafruit_sht31d

kSeaLevelPressure = 1013.25
kAltitude = 1645
kMicSampleFrequency = 16000
kMicSampleDurationS = 0.1
kSampleArray = array.array("H",
                           [0] * int(kMicSampleFrequency * kMicSampleDurationS))


def normalized_rms(values):
    minbuf = int(sum(values) / len(values))
    return int(
        math.sqrt(
            sum(
                float(sample - minbuf) * (sample - minbuf) for sample in values)
            / len(values)))


class Sensors:

    def __init__(self):
        i2c = board.I2C()
        self.apds9960 = adafruit_apds9960.apds9960.APDS9960(i2c)
        self.apds9960.enable_proximity = True
        self.apds9960.enable_color = True
        self.bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
        self.bmp280.sea_level_pressure = kSeaLevelPressure
        self.lis3mdl = adafruit_lis3mdl.LIS3MDL(i2c)
        self.lsm6ds33 = adafruit_lsm6ds.lsm6ds33.LSM6DS33(i2c)
        self.sht31d = adafruit_sht31d.SHT31D(i2c)
        self.microphone = audiobusio.PDMIn(
            board.MICROPHONE_CLOCK,
            board.MICROPHONE_DATA,
            sample_rate=kMicSampleFrequency,
            bit_depth=16,
        )
        print("Sensors initialized!")

    def getProximity(self):
        return self.apds9960.proximity

    def getColors(self):
        r, g, b, c = self.apds9960.color_data
        # Correct for intensity variation of sensor according to datasheet.
        r = min(65535, int(r * 1.333))
        g = min(65535, int(g * 1.333))
        b = min(65535, int(b * 2.778))
        return [r, g, b, c]

    def getTemperature(self):
        return self.bmp280.temperature

    def getStationPressure(self):
        return self.bmp280.pressure

    def getBaroPressure(self):
        temperature = self.getTemperature()
        station_pressure = self.getStationPressure()
        return station_pressure / math.exp(-kAltitude /
                                           ((273.15 + temperature) * 29.263))

    def getAltitude(self):
        return self.bmp280.altitude

    def getMagnetic(self):
        return np.array(self.lis3mdl.magnetic)

    def getAccel(self):
        return np.array(self.lsm6ds33.acceleration)

    def getGyro(self):
        return np.array(self.lsm6ds33.gyro)

    def getHumidity(self):
        return self.sht31d.relative_humidity

    def getHumidityShort(self):
        return min(65535, max(0, int(self.getHumidity() * 655.35)))

    def getLoudness(self):
        # samples = array.array("H", [0] *
        #                       int(kMicSampleFrequency * kMicSampleDurationS))
        self.microphone.record(kSampleArray, len(kSampleArray))
        return normalized_rms(kSampleArray)

    def get9DoF(self):
        state = np.zeros((1, 9))
        state[0, 0:3] = self.getAccel()
        state[0, 3:6] = self.getMagnetic()
        state[0, 6:9] = self.getGyro()
        return state

    def getEnvironmentalAsVector(self):
        colors = self.getColors()
        return np.array((
            colors[0],
            colors[1],
            colors[2],
            colors[3],
            self.getTemperature(),
            self.getBaroPressure(),
            self.getHumidity(),
            self.getLoudness(),
        ))

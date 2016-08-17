"""
Generic class to support analogue sensors.

The MCP3008 ADC is used by this class, and output can be in
either Ohms or millivolts depending on the exact sensor in question.

"""
import mcp3008
import sensor
import time

class Analogue(sensor.Sensor):
    """ The MCP3008 ADC is used by this class, and output can be in
    either Ohms or millivolts depending on the exact sensor in question.

    """
    requiredData = ["adcpin", "measurement", "sensorname"]
    optionalData = ["pullupResistance", "pulldownResistance", "sensorvoltage", "description"]

    def __init__(self, data):
        """Initialise.

        Initialise the generic Analogue sensor class using parameters passed
        in 'data'.

        Args:
            self: self.
            data: A dict containing the parameters to be used during setup.

        """
        self.adc = mcp3008.MCP3008.sharedClass
        self.adcpin = int(data["adcpin"])
        self.valname = data["measurement"]
        self.sensorname = data["sensorname"]
        self.readingtype = "sample"
        self.pullup, self.pulldown = None, None
        if "pullupResistance" in data:
            self.pullup = int(data["pullupResistance"])
        if "pulldownResistance" in data:
            self.pulldown = int(data["pulldownResistance"])
        if "sensorvoltage" in data:
            self.sensorvoltage = int(data["sensorvoltage"])
        else:
            self.sensorvoltage = 3.3

        class ConfigError(Exception):
            """ Exception to raise if no pullup or pulldown value."""
            pass

        if self.pullup != None and self.pulldown != None:
            msg = "Please choose whether there is a pull up or pull down"
            msg += " resistor for the " + self.valname + " measurement by only"
            msg += " entering one of them into the settings file"
            print(msg)
            raise ConfigError
        self.valunit = "Ohms"
        self.valsymbol = "Ohms"
        if self.pullup == None and self.pulldown == None:
            self.valunit = "millvolts"
            self.valsymbol = "mV"
        if "description" in data:
            self.description = data["description"]
        else:
            self.description = "An analogue sensor."

    def getval(self):
        """Get the current sensor value.

        Get the current sensor value, in either Ohms or millivolts depending
        on the exact sensor. Includes a 'sense check' to identify
        potential errors with full or no voltage.

        Args:
            self: self.

        Returns:
            float The current value for the sensor.
            None If there is potentially an error with the data.

        """
        """
        result = 0.0
        readings = 0.0
        readingsc = 0.0
        for i in range(0, 3):
            reading = self.adc.readadc(self.adcpin)
            if (reading != 0 and reading != 1023):
                readings = readings + reading
                readingsc = readingsc + 1
            time.sleep(0.5)
        if readingsc == 0:
        """

        result = self.adc.readadc(self.adcpin)

        """
        else:
            result = readings / readingsc
        """
        if result == 0:
            msg = "Error: Check wiring for the " + self.sensorname
            msg += " measurement, no voltage detected on ADC input "
            msg += str(self.adcpin)
            print(msg)
            return None
        if result == 1023:
            if self.sensorname == "LDR":
                # Carrying on with 1023 gives divide by zero error below
                result = 1022
            else:
                msg = "Error: Check wiring for the " + self.sensorname
                msg += " measurement, full voltage detected on ADC input "
                msg += str(self.adcpin)
                print(msg)
                return None
        vout = float(result)/1023 * 3.3

        if self.sensorname == "WindDirection":
            return self.getWindDirection(self.pullup / ((self.sensorvoltage / vout) - 1))

        if self.pulldown != None:
            resout = (self.pulldown * self.sensorvoltage) / vout - self.pulldown
        elif self.pullup != None:
            resout = self.pullup / ((self.sensorvoltage / vout) - 1)
        else:
            resout = vout * 1000
        return resout

    def getWindDirection(self, ohm):
        directions = { 9700: 22.5, 12450: 45, 1185: 67.5, 1390: 90, 980: 112.5, 3200: 135, 1990: 157.5, 5680: 180, 4600: 202.5, 25000: 225, 21800: 247.5, 385000: 270, 76000: 292.5, 133000: 315, 35000: 337.5, 56500: 360 }

        bestDiff = 1000000
        bestVal = 0

        for key, value in directions.iteritems():
            diff = abs(key - ohm)
            if diff < bestDiff:
                bestDiff = diff
                bestVal = value

        return bestVal

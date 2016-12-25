"""
Generic class to support analogue sensors.

The MCP3008 ADC is used by this class, and output can be in
either Ohms or millivolts depending on the exact sensor in question.

"""
import mcp3008
import sensor
import time
import operator
import dustBackend
import microphone

class Analogue(sensor.Sensor):
    """ The MCP3008 ADC is used by this class, and output can be in
    either Ohms or millivolts depending on the exact sensor in question.

    """
    requiredData = ["adcpin", "measurement", "sensorname"]
    optionalData = ["pullupResistance", "pulldownResistance", "sensorvoltage", "description", "averagingAttemps", "averagingTimeout", "averagingMethod", "digpin"]

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
        self.digpin = 0
        if "digpin" in data:
            self.digpin = int(data["digpin"])
        self.averagingAttemps = 0
        if "averagingAttemps" in data:
            self.averagingAttemps = int(data["averagingAttemps"])
        self.averagingTimeout = 0.0
        if "averagingTimeout" in data:
            self.averagingTimeout = float(data["averagingTimeout"])
        self.averagingMethod = "avg"
        if "averagingMethod" in data:
            self.averagingMethod = data["averagingMethod"]
        self.readingtype = "sample"
        self.pullup, self.pulldown = None, None
        if "pullupResistance" in data:
            self.pullup = int(data["pullupResistance"])
        if "pulldownResistance" in data:
            self.pulldown = int(data["pulldownResistance"])
        if "sensorvoltage" in data:
            self.sensorvoltage = float(data["sensorvoltage"])
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
        
        if self.averagingAttemps > 1:
            result = 0.0
            readings = 0.0
            readingsc = 0.0
	    readings_array = {}
            for i in range(0, self.averagingAttemps):
                reading = self.getReading()
                if (reading != 0 and reading != 1023):
                    if self.averagingMethod == "max":
                        if reading > readings:
			    """print(str(reading) + " higher as " + str(readings))"""
                            readings = reading
                    else:
                        readings = readings + reading
                    readingsc = readingsc + 1
		    if reading in readings_array:
		        readings_array[reading] = readings_array[reading] + 1
		    else:
			readings_array[reading] = 1
                time.sleep(self.averagingTimeout)
            if readingsc == 0:
                result = self.getReading()
            else:
		if self.averagingMethod == "most":
		    sorted_x = sorted(readings_array.items(), key=operator.itemgetter(1), reverse=True)
		    result = sorted_x[0][0]
                elif self.averagingMethod == "max":
                    result = readings
                else:
                    result = readings / readingsc
        else:
            result = self.getReading()
        
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

	if self.sensorname == "WindDirection":
	    return result

	"""print(self.sensorname + " " + str(self.sensorvoltage))"""

        vout = float(result)/1023 * self.sensorvoltage
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

    def getReading(self):
	if self.sensorname == "Dust":
	    dus = dustBackend.DustBackend(self.adcpin, self.digpin)
	    return dus.Fetch()
	elif self.sensorname == "Microphone":
	    mic = microphone.Microphone(self.adcpin)
	    return mic.Fetch()

	reading = self.adc.readadc(self.adcpin)

	if (self.sensorname == "WindDirection" and reading != 0 and reading != 1023):
            vout = float(reading)/1023 * 3.3
            return self.getWindDirection(self.pullup / ((self.sensorvoltage / vout) - 1))

	return reading
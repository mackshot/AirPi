""" Read data from TSL2561 sensor. """
import sensor
import TSL2561Backend

class TSL2561(sensor.Sensor):
    """ Read data from TSL2561 sensor. """

    tslClass = None
    requiredData = ["measurement", "i2cbus"]
    optionalData = ["unit", "description"]

    def __init__(self, data):
        self.readingtype = "sample"
        if "lux" in data["measurement"].lower():
            self.sensorname = "TSL2561-lux"
            self.valname = "Lux-TSL2561"
            self.valunit = "Lux"
            self.valsymbol = "Lux"
        self.description = data["description"]
        if TSL2561.tslClass == None:
            TSL2561.tslClass = TSL2561Backend.TSL2561(bus=int(data["i2cbus"]))
        return

    def getval(self):
        if self.valname == "Lux-TSL2561":
            temp = TSL2561.tslClass.readLux()
            return temp

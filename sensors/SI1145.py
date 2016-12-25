""" Read data from SI1145 sensor. """
import sensor
import SI1145Backend

class SI1145(sensor.Sensor):
    """ Read data from SI1145 sensor. """

    siClass = None
    requiredData = ["measurement", "i2cbus"]
    optionalData = ["unit", "description"]

    def __init__(self, data):
        self.readingtype = "sample"
        if "uvi" in data["measurement"].lower():
            self.sensorname = "SI1145-uvi"
            self.valname = "UVI-SI1145"
            self.valunit = "UVI*100"
            self.valsymbol = "UVI"
        self.description = data["description"]
        if SI1145.siClass == None:
            SI1145.siClass = SI1145Backend.SI1145(bus=int(data["i2cbus"]))
        return

    def getval(self):
        if self.valname == "UVI-SI1145":
            temp = SI1145.siClass.readUV()
            return temp

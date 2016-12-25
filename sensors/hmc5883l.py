""" Read data from hmc5883l sensor. """
import sensor
import hmc5883lBackend
import math

class hmc5883l(sensor.Sensor):
    """ Read data from hmc5883l sensor. """

    hmcClass = None
    requiredData = ["measurement", "i2cbus","declination_degrees","declination_minutes"]
    optionalData = ["unit", "description"]

    def __init__(self, data):
        self.readingtype = "sample"
        if "total" in data["measurement"].lower():
            self.sensorname = "hmc5883l-total"
            self.valname = "Tesla-Total-hmc5883l"
            self.valunit = "Nano Tesla"
            self.valsymbol = "nT"
        elif "x" in data["measurement"].lower():
            self.sensorname = "hmc5883l-x"
            self.valname = "Tesla-X-hmc5883l"
            self.valunit = "Nano Tesla"
            self.valsymbol = "nT"
        elif "y" in data["measurement"].lower():
            self.sensorname = "hmc5883l-y"
            self.valname = "Tesla-Y-hmc5883l"
            self.valunit = "Nano Tesla"
            self.valsymbol = "nT"
        elif "z" in data["measurement"].lower():
            self.sensorname = "hmc5883l-z"
            self.valname = "Tesla-Z-hmc5883l"
            self.valunit = "Nano Tesla"
            self.valsymbol = "nT"
        elif "direction" in data["measurement"].lower():
            self.sensorname = "hmc5883l-direction"
            self.valname = "Compass-hmc5883l"
            self.valunit = "Grad"
            self.valsymbol = "Grad"
        self.description = data["description"]
        if hmc5883l.hmcClass == None:
            hmc5883l.hmcClass = hmc5883lBackend.hmc5883l(bus=int(data["i2cbus"]),declination=(int(data["declination_degrees"]),int(data["declination_minutes"])))
        return

    def getval(self):
        if self.valname == "Tesla-Total-hmc5883l":
            temp = hmc5883l.hmcClass.axes()
            gauss = round(math.sqrt(temp[0] * temp[0] + temp[1] * temp[1] + temp[2] * temp[2]), 2)
	    return math.floor(gauss * 100)
        elif self.valname == "Tesla-X-hmc5883l":
            temp = hmc5883l.hmcClass.axes()
            gauss = temp[0]
	    return math.floor(gauss * 100)
        elif self.valname == "Tesla-Y-hmc5883l":
            temp = hmc5883l.hmcClass.axes()
            gauss = temp[1]
	    return math.floor(gauss * 100)
        elif self.valname == "Tesla-Z-hmc5883l":
            temp = hmc5883l.hmcClass.axes()
            gauss = temp[2]
	    return math.floor(gauss * 100)
        elif self.valname == "Compass-hmc5883l":
            temp = hmc5883l.hmcClass.heading()
            return temp
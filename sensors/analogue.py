from . import mcp3008
from . import sensor

class Analogue(sensor.Sensor):
    requireddata = ["adcPin", "measurement", "sensorName"]
    optionaldata = ["pullUpResistance", "pullDownResistance", "sensorVoltage", "description"]
    
    def __init__(self, data):
        self.adc = mcp3008.MCP3008.sharedclass
        self.adcpin = int(data['adcPin'])
        self.valname = data['measurement']
        self.sensorname = data['sensorName']
        self.readingtype = "sample"
        self.pullup, self.pulldown = None, None
        if "pullupresistance" in data:
            self.pullup = int(data['pullUpResistance'])
        if "pulldownresistance" in data:
            self.pulldown = int(data['pullDownResistance'])
        if "sensorvoltage" in data:
            self.sensorvoltage = int(data['sensorVoltage'])
        else:
            self.sensorvoltage = 3.3
        class ConfigError(Exception): pass
        if self.pullup != None and self.pulldown != None:
            print("Please choose whether there is a pull up or pull down resistor for the " + self.valname + " measurement by only entering one of them into the settings file")
            raise ConfigError
        self.valunit = "Ohms"
        self.valsymbol = "Ohms"
        if self.pullup == None and self.pulldown == None:
            self.valunit = "millvolts"
            self.valsymbol = "mV"
        if "description" in data:
            self.description = data['description']
        else:
            self.description = "An analogue sensor."
        
    def getval(self):
        result = self.adc.readadc(self.adcpin)
        if result == 0:
            print("Error: Check wiring for the " + self.sensorname + " measurement, no voltage detected on ADC input " + str(self.adcpin))
            return None
        if result == 1023 or result == 1022:
            print("Error: Check wiring for the " + self.sensorname + " measurement, full voltage detected on ADC input " + str(self.adcpin))
            return None
        vout = float(result)/1023 * 3.3
        
        if self.pulldown!=None:
            #Its a pull down resistor
            resout = (self.pulldown * self.sensorvoltage) / vout - self.pulldown
        elif self.pullup!=None:
            resout = self.pullup / ((self.sensorvoltage / vout) - 1)
        else:
            resout = vout * 1000
        return resout
        

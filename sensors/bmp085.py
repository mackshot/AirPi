from . import sensor
from . import bmpBackend

class BMP085(sensor.Sensor):
	bmpclass = None
	requireddata = ["measurement", "i2cbus"]
	optionaldata = ["altitude", "mslp", "unit", "description"]
	def __init__(self, data):
		self.sensorname = "BMP085"
		self.readingtype = "sample"
		if "temp" in data['measurement'].lower():
			self.valname = "Temperature"
			self.valunit = "Celsius"
			self.valsymbol = "C"
			if "unit" in data:
				if data['unit'] == "F":
					self.valunit = "Fahrenheit"
					self.valsymbol = "F"
		elif "pres" in data['measurement'].lower():
			self.valname = "Pressure"
			self.valsymbol = "hPa"
			self.valunit = "Hectopascal"
			self.altitude = 0
			self.mslp = False
			if "mslp" in data:
				if data['mslp'].lower() in ['on", "true", "1", "yes']:
					self.mslp = True
					if "altitude" in data:
						self.altitude = data['altitude']
					else:
						print("To calculate MSLP, please provide an 'altitude' config setting (in m) for the BMP085 pressure module")
						self.mslp = False
		if "description" in data:
			self.description = data['description']
		else:
			self.description = "BOSCH combined temperature and pressure sensor."
		if (BMP085.bmpclass == None):
			BMP085.bmpclass = bmpBackend.BMP085(bus = int(data['i2cbus']))
		return

	def getval(self):
		if self.valname == "Temperature":
			temp = BMP085.bmpclass.readtemperature()
			if self.valunit == "Fahrenheit":
				temp = temp * 1.8 + 32
			return temp
		elif self.valname == "Pressure":
			if self.mslp:
				return BMP085.bmpclass.readmslpressure(self.altitude) * 0.01 #to convert to Hectopascals
			else:
				return BMP085.bmpclass.readpressure() * 0.01 #to convert to Hectopascals

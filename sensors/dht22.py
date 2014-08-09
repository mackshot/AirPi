from . import sensor
from . import Raspberry_Pi_Driver as dhtreader
import time
import threading

# https://github.com/adafruit/Adafruit-Raspberry-Pi-Python-Code/blob/master/Adafruit_DHT_Driver_Python/dhtreader.c
# https://github.com/guillier/Adafruit_Python_DHT

class DHT22(sensor.Sensor):
	requireddata = ["measurement", "pinNumber"]
	optionaldata = ["unit", "description"]
	
	def __init__(self,data):
		dhtreader.init()
		dhtreader.lastdatatime = 0
		dhtreader.lastdata = (None, None)
		self.sensorname = "DHT22"
		self.readingtype = "sample"
		self.pinnum = int(data['pinNumber'])
		if "temp" in data['measurement'].lower():
			self.valname = "Temperature"
			self.valunit = "Celsius"
			self.valsymbol = "C"
			if "unit" in data:
				if data['unit'] == "F":
					self.valunit = "Fahrenheit"
					self.valsymbol = "F"
		elif "h" in data['measurement'].lower():
			self.valname = "Relative Humidity"
			self.valsymbol = "%"
			self.valunit = "% Relative Humidity"
		if "description" in data:
			self.description = data['description']
		else:
			self.description = "A combined temperature and humidity sensor."
		return

	def getval(self):
		if (time.time() - dhtreader.lastdatatime) > 2: # ok to do another reading
			# launch & wait for thread
			th = DHTReadThread(self)
			th.start()
			th.join(2)
			if th.isAlive():
				raise Exception('Timeout reading ' + self.sensorname)
			dhtreader.lastdatatime = time.time()

		t, h = dhtreader.lastdata
		if self.valname == "Temperature":
			temp = t
			if self.valunit == "Fahrenheit":
				temp = temp * 1.8 + 32
			return temp
		elif self.valname == "Relative Humidity":
			return h

# http://softwareramblings.com/2008/06/running-functions-as-threads-in-python.html
# https://docs.python.org/2/library/threading.html
class DHTReadThread(threading.Thread):
	def __init__(self, parent):
		self.parent = parent
		threading.Thread.__init__(self)

	def run(self):
		try:
			t, h = dhtreader.read(22,self.parent.pinnum)
		except Exception:
			t, h = dhtreader.lastdata
		dhtreader.lastdata = (t,h)

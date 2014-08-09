import RPi.GPIO as GPIO
from . import sensor

class raingauge(sensor.Sensor):
	requireddata = ["pinNumber"]
	optionaldata = ["description"]
    
	def __init__(self, data):
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		self.pinnum = int(data['pinNumber'])
		GPIO.setup(self.pinnum, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		GPIO.add_event_detect(self.pinnum, GPIO.FALLING, callback=self.buckettip, bouncetime=300)
		self.rain = 0
		self.sensorname = "Maplin_N77NF"
		self.readingtype = "pulseCount"
		self.valname = "Bucket_tips"
		self.valsymbol = ""
		self.valunit = ""
		if "description" in data:
			self.description = data['description']
		else:
			self.description = "A rain gauge."

	def getval(self):
	        # return number of bucket tips since last reading
	        # that means we reset the count at this reading
		rain = self.rain
		self.rain = 0
		return rain

	def buckettip(self, channel):
		self.rain += 1


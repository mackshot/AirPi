"""
Generic class to support analogue sensors.

The MCP3008 ADC is used by this class, and output can be in
either Ohms or millivolts depending on the exact sensor in question.

"""
import RPi.GPIO as GPIO
import mcp3008
import sensor
import time
import operator

class DustBackend:

    def __init__(self, adcpin = 6, digital_pin = 7):
	self.adc = mcp3008.MCP3008.sharedClass
	self.analogue_pin = adcpin
	self.digital_pin = digital_pin
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(self.digital_pin, GPIO.OUT)

    def Run(self):
	while 1 == 1:
	    print(self.Fetch())
	    time.sleep(0.1)

    def Fetch(self):
	GPIO.output(self.digital_pin, GPIO.LOW)
	time.sleep(0.000028)
	voMeasured = self.adc.readadc(self.analogue_pin)
	time.sleep(0.000004)
	GPIO.output(self.digital_pin, GPIO.HIGH)
	time.sleep(0.000968)
	return voMeasured

v = mcp3008.MCP3008({})

#d = DustBackend()
#d.Run()

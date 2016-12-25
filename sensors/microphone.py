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

class Microphone:

    def __init__(self, adcpin):
	self.adc = mcp3008.MCP3008.sharedClass
	self.analogue_pin = adcpin

    def Run(self):
	while 1 == 1:
	    print(self.Fetch())
	    time.sleep(0.1)

    def Fetch(self):

	signalMin = 1024
	signalMax = 0
	start = time.time()

	while ((time.time() - start) * 1000) < 100:
	    reading = self.adc.readadc(self.analogue_pin)

	    if reading >= 1023:
		continue

	    if signalMin > reading:
	        signalMin = reading
	    if signalMax < reading:
	        signalMax = reading

	return (signalMax - signalMin)

v = mcp3008.MCP3008({})


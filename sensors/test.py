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
import microphone

v = mcp3008.MCP3008({})

t = microphone.Microphone(2)

t.Run()

print(t.Fetch())
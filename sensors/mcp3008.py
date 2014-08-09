import RPi.GPIO as GPIO
from . import sensor

class MCP3008(sensor.Sensor):
    requireddata = []
    optionaldata = ["mosiPin", "misoPin", "csPin", "clkPin"]
    sharedclass = None

    def __init__(self, data):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.spimosi = 23
        self.spimoso = 24
        self.spiclk = 18
        self.spics = 25
        if "mosiPin" in data:
            self.spimosi = data['mosiPin']
        if "misoPin" in data:
            self.spimoso = data['misoPin']
        if "clkPin" in data:
            self.spiclk = data['clkPin']
        if "csPin" in data:
            self.spics = data['csPin']
        GPIO.setup(self.spimosi, GPIO.OUT)
        GPIO.setup(self.spimoso, GPIO.IN)
        GPIO.setup(self.spiclk, GPIO.OUT)
        GPIO.setup(self.spics, GPIO.OUT)
        if MCP3008.sharedclass == None:
            MCP3008.sharedclass = self


    #read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
    def readadc(self,adcnum):
        if ((adcnum > 7) or (adcnum < 0)):
            return -1
        GPIO.output(self.spics, True)

        GPIO.output(self.spiclk, False)  # start clock low
        GPIO.output(self.spics, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
            if (commandout & 0x80):
                GPIO.output(self.spimosi, True)
            else:
                GPIO.output(self.spimosi, False)
            commandout <<= 1
            GPIO.output(self.spiclk, True)
            GPIO.output(self.spiclk, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(11):
            GPIO.output(self.spiclk, True)
            GPIO.output(self.spiclk, False)
            adcout <<= 1
            if (GPIO.input(self.spimoso)):
                adcout |= 0x1

        GPIO.output(self.spics, True)
        return adcout

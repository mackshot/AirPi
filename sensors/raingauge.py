""" Work with a raingauge.

Work with a (Maplin) raingauge, i.e. read data and record bucket tips.
The gauge is connected directly to a GPIO pin (and ground).

Originally written by Fred Sonnenwald <f.sonnenwald@sheffield.ac.uk>
https://pi.gate.ac.uk/posts/2014/04/21/airpisoftware/
https://pi.gate.ac.uk/posts/2014/01/25/raingauge/
http://www.maplin.co.uk/p/maplin-replacement-rain-gauge-for-n25frn96fyn96gy-n77nf

"""
import RPi.GPIO as GPIO
import sensor

class Raingauge(sensor.Sensor):
    """ Work with a raingauge.

    Work with a (Maplin) raingauge, i.e. read data and record bucket tips.
    The gauge is connected directly to a GPIO pin (and ground).

    Originally written by Fred Sonnenwald <f.sonnenwald@sheffield.ac.uk>
    https://pi.gate.ac.uk/posts/2014/04/21/airpisoftware/
    https://pi.gate.ac.uk/posts/2014/01/25/raingauge/
    http://www.maplin.co.uk/p/maplin-replacement-rain-gauge-for-n25frn96fyn96gy-n77nf

    """
    requiredData = ["pinnumber"]
    optionalData = ["description"]

    def __init__(self, data):
        """Initialise.

        Initialise the raingauge sensor Class using parameters passed in 'data'.

        Args:
            self: self.
            data: A dict containing the parameters to be used during setup.

        Return:

        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.pinnum = int(data["pinnumber"])
        GPIO.setup(self.pinnum, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pinnum, GPIO.FALLING, callback=self.buckettip, bouncetime=300)
        self.rain = 0.0000001
        self.sensorname = "Raingauge"
        self.readingtype = "pulseCount"
        self.valname = "Bucket_tips"
        self.valsymbol = ""
        self.valunit = ""
        if "description" in data:
            self.description = data["description"]
        else:
            self.description = "A rain gauge."

    def getval(self):
        """Get no. of tips *since last reading*.

        Get the current sensor value, which is the number of bucket tips
        since the last reading. Note that it is NOT the total number of
        bucket tips since the start of the run. Once this is done, reset
        the count.

        Args:
            self: self.

        Returns:
            float The current value for the sensor.

        """

        rain = self.rain
        self.rain = 0.0000001
        return rain

    def buckettip(self, channel):
        """Record a bucket tip.

        Record a bucket tip. Note that "channel" must always be passed to this
        function, for reasons which aren't particularly clear in the docs:
        http://raspi.tv/2013/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio-part-3#comment-18986
        http://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/

        """
        self.rain += 1.0
        print("rain",self.rain,self.pinnum)

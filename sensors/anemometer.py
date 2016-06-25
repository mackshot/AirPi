""" Work with a anemometer.

Work with a (Maplin) anemometer, i.e. read data and pulse counts, i.e. rotations.
The anemometer is connected directly to a GPIO pin (and ground).

"""
import RPi.GPIO as GPIO
import sensor

class Anemometer(sensor.Sensor):
    """ Work with a anemometer.

    """
    requiredData = ["pinnumber"]
    optionalData = ["description"]

    def __init__(self, data):
        """Initialise.

        Initialise the anemometer sensor Class using parameters passed in 'data'.

        Args:
            self: self.
            data: A dict containing the parameters to be used during setup.

        Return:

        """
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.pinnum = int(data["pinnumber"])
        GPIO.setup(self.pinnum, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pinnum, GPIO.FALLING, callback=self.rotate, bouncetime=300)
        self.rotations = 0.0000001
        self.sensorname = "Anemometer"
        self.readingtype = "pulseCount"
        self.valname = "Rotations"
        self.valsymbol = ""
        self.valunit = ""
        if "description" in data:
            self.description = data["description"]
        else:
            self.description = "An anemometer."

    def getval(self):
        """Get no. of rotations *since last reading*.

        Get the current sensor value, which is the number of rotations
        since the last reading. Note that it is NOT the total number of
        rotations since the start of the run. Once this is done, reset
        the count.

        Args:
            self: self.

        Returns:
            float The current value for the sensor.

        """

        rotations = self.rotations
        self.rotations = 0.0000001
        return rotations

    def rotate(self, channel):
        """Record a rotations

        Record a rotation. Note that "channel" must always be passed to this
        function, for reasons which aren't particularly clear in the docs:
        http://raspi.tv/2013/how-to-use-interrupts-with-python-on-the-raspberry-pi-and-rpi-gpio-part-3#comment-18986
        http://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/

        """
        self.rotations += 1.0

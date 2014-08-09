#!/usr/bin/env python

"""This file takes in inputs from a variety of sensor files,
   and outputs information to a variety of services.

"""

import sys
sys.dont_write_bytecode = True

import RPi.GPIO as GPIO
import configparser
import time
import inspect
import os
import signal
import urllib.request
import logging, logging.handlers
from datetime import datetime
from math import isnan
from sensors import sensor
from outputs import output
from notifications import notification

CFGDIR = '/home/pi/AirPi3'
SENSORSCFG = os.path.join(CFGDIR, 'sensors.cfg')
OUTPUTSCFG = os.path.join(CFGDIR, 'outputs.cfg')
SETTINGSCFG = os.path.join(CFGDIR, 'settings.cfg')
NOTIFICATIONSCFG = os.path.join(CFGDIR, 'notifications.cfg')

LOG_FILENAME = os.path.join(CFGDIR, 'airpi.log')
# Set up a specific LOGGER with our desired output level
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
# create HANDLER and add it to the LOGGER
HANDLER = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=40960, backupCount=5)
LOGGER.addHandler(HANDLER)
# create FORMATTER and add it to the HANDLER
FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
HANDLER.setFormatter(FORMATTER)
# Uncomment below for more verbose logging output
# logging.basicConfig(level=logging.DEBUG)

def interrupt_handler(signal, frame):
    """Handle the Ctrl+C KeyboardInterrupt by exiting."""
    if gpsplugininstance:
        gpsplugininstance.stopController()
    GPIO.output(GREENPIN, GPIO.LOW)
    GPIO.output(REDPIN, GPIO.LOW)
    print(os.linesep)
    print("Stopping sampling as requested...")
    sys.exit(1)

def get_subclasses(mod, cls):
    """Load subclasses for a module.

    Load the named subclasses for a specified module.

    Args:
        mod: Module from which subclass should be loaded.
        cls: Subclass to load

    Returns:
        The subclass.

    """
    for name, obj in inspect.getmembers(mod):
        if hasattr(obj, "__bases__") and cls in obj.__bases__:
            return obj

def check_conn():
    """Check internet connectivity.

    Check for internet connectivity by trying to connect to a website.

    Returns:
        Boolean True if successfully connects to the site within five seconds.
        Boolean False if fails to connect to the site within five seconds.

    """
    try:
        urllib.request.urlopen("http://www.google.com", timeout=5)
        return True
    except URLError as err:
        pass
    return False

class MissingField(Exception):
    """Exception to be raised when an imported plugin is missing a required
    field.
    """
    pass

if not os.path.isfile(SENSORSCFG):
    msg = "Unable to access config file: " + SENSORSCFG
    print(msg)
    LOGGER.error(msg)
    exit(1)

SENSORCONFIG = configparser.SafeConfigParser()
SENSORCONFIG.read(SENSORSCFG)

sensornames = SENSORCONFIG.sections()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) #Use BCM GPIO numbers.

sensorplugins = []
gpsplugininstance = None

for i in sensornames:
    try:
        try:
            filename = SENSORCONFIG.get(i, "filename")
        except Exception:
            msg = "Error: no filename config option found for"
            msg += " sensor plugin " + str(i)
            print(msg)
            LOGGER.error(msg)
            raise
        try:
            enabled = SENSORCONFIG.getboolean(i, "enabled")
        except Exception:
            enabled = True

        #if enabled, load the plugin
        if enabled:
            try:
                # 'a' means nothing below, but argument must be non-null
                mod = __import__('sensors.' + filename, fromlist=['a'])
            except Exception as excep:
                msg = "Error: could not import sensor module " + filename
                msg += ": " + str(excep)
                print(msg)
                LOGGER.error(msg)
                raise

            try:
                sensorclass = get_subclasses(mod, sensor.Sensor)
                if sensorclass == None:
                    raise AttributeError
            except Exception:
                msg = "Error: could not find a subclass of sensor.Sensor"
                msg += " in module" + filename
                print(msg)
                LOGGER.error(msg)
                raise

            try:
                reqd = sensorclass.requireddata
            except Exception:
                reqd = []
            try:
                opt = sensorclass.optionaldata
            except Exception:
                opt = []

            plugindata = {}

            for reqdfield in reqd:
                if SENSORCONFIG.has_option(i, reqdfield):
                    plugindata[reqdfield] = SENSORCONFIG.get(i, reqdfield)
                else:
                    msg = "Error: Missing required field '" + reqdfield
                    msg += "' for sensor plugin " + i + "." + os.linesep
                    msg += "Error: This should be found in file: " + SENSORSCFG
                    print(msg)
                    LOGGER.error(msg)
                    raise MissingField
            for optfield in opt:
                if SENSORCONFIG.has_option(i, optfield):
                    plugindata[optfield] = SENSORCONFIG.get(i, optfield)
            instclass = sensorclass(plugindata)
            # check for a getval
            if callable(getattr(instclass, "getval", None)):
                sensorplugins.append(instclass)
                # store sensorplugins array length for GPS plugin
                if i == "GPS":
                    gpsplugininstance = instclass
                msg = "Success: Loaded sensor plugin " + str(i)
                print(msg)
                LOGGER.info(msg)
            else:
                msg = "Success: Loaded support plugin " + str(i)
                print(msg)
                LOGGER.info(msg)
    except Exception as excep: #add specific exception for missing module
        msg = "Error: Did not import sensor plugin " + str(i) + ": " + str(excep)
        print(msg)
        LOGGER.error(msg)
        raise excep



if not os.path.isfile(OUTPUTSCFG):
    msg = "Unable to access config file: " + OUTPUTSCFG
    print(msg)
    LOGGER.error(msg)
    exit(1)

OUTPUTCONFIG = configparser.SafeConfigParser()
OUTPUTCONFIG.read(OUTPUTSCFG)

outputnames = OUTPUTCONFIG.sections()

outputplugins = []

metadata = None

for i in outputnames:
    try:
        try:
            filename = OUTPUTCONFIG.get(i, "filename")
        except Exception:
            msg = "Error: no filename config option found for"
            msg += " output plugin " + str(i)
            print(msg)
            LOGGER.error(msg)
            raise
        try:
            enabled = OUTPUTCONFIG.getboolean(i, "enabled")
        except Exception:
            enabled = True

        #if enabled, load the plugin
        if enabled:
            try:
                # 'a' means nothing below, but argument must be non-null
                mod = __import__('outputs.' + filename, fromlist=['a'])
            except Exception:
                msg = "Error: could not import output module " + filename
                print(msg)
                LOGGER.error(msg)
                raise

            try:
                outputclass = get_subclasses(mod, output.Output)
                if outputclass == None:
                    raise AttributeError
            except Exception:
                msg = "Error: could not find a subclass of output.Output"
                msg += " in module " + filename
                print(msg)
                LOGGER.error(msg)
                raise

            try:
                reqd = outputclass.requiredparams
            except Exception:
                reqd = []
            try:
                opt = outputclass.optionalparams
            except Exception:
                opt = []
            if OUTPUTCONFIG.has_option(i, "async"):
                async = OUTPUTCONFIG.getboolean(i, "async")
            else:
                async = False

            plugindata = {}
            for reqdfield in reqd:
                if OUTPUTCONFIG.has_option(i, reqdfield):
                    plugindata[reqdfield] = OUTPUTCONFIG.get(i, reqdfield)
                else:
                    msg = "Error: Missing required field '" + reqdfield
                    msg += "' for output plugin " + str(i) + "." + os.linesep
                    msg += "Error: This should be found in file: " + OUTPUTSCFG
                    print(msg)
                    LOGGER.error(msg)
                    raise MissingField
            for optfield in opt:
                if OUTPUTCONFIG.has_option(i, optfield):
                    plugindata[optfield] = OUTPUTCONFIG.get(i, optfield)

            if OUTPUTCONFIG.has_option(i, "needsinternet"):
                if OUTPUTCONFIG.getboolean(i, "needsinternet"):
                    if not check_conn():
                        msg = "Error: Skipping output plugin " + i
                        msg += " because no internet connectivity."
                        print(msg)
                        LOGGER.info(msg)
            else:
                instclass = outputclass(plugindata)
                instclass.async = async

                # check for a outputdata() function
                if callable(getattr(instclass, "outputdata", None)):
                    outputplugins.append(instclass)
                    msg = "Success: Loaded output plugin " + str(i)
                    print(msg)
                    LOGGER.info(msg)
                else:
                    msg = "Success: Loaded support plugin " + str(i)
                    print(msg)
                    LOGGER.info(msg)

                # Check for an outputmetadata function
                if OUTPUTCONFIG.has_option(i, "metadatareqd"):
                    if OUTPUTCONFIG.getboolean(i, "metadatareqd"):
                        if callable(getattr(instclass, "outputmetadata", None)):
                            # We'll printthis later on
                            metadata = instclass.outputmetadata()

    except Exception as excep: #add specific exception for missing module
        msg = "Error: Did not import output plugin " + str(i) + ": " + str(excep)
        print(msg)
        LOGGER.error(msg)
        raise excep

if not outputplugins:
    msg = "There are no output plugins enabled!"
    msg += " Please enable at least one in " + OUTPUTSCFG + " and try again."
    print(msg)
    LOGGER.error(msg)
    sys.exit(1)

if not os.path.isfile(NOTIFICATIONSCFG):
    msg = "Unable to access config file: " + NOTIFICATIONSCFG
    print(msg)
    LOGGER.error(msg)
    exit(1)

NOTIFICATIONCONFIG = configparser.SafeConfigParser()
NOTIFICATIONCONFIG.read(NOTIFICATIONSCFG)

notificationnames = NOTIFICATIONCONFIG.sections()
notificationnames.remove("Common")

notificationplugins = []

for i in notificationnames:
    try:
        try:
            filename = NOTIFICATIONCONFIG.get(i, "filename")
        except Exception:
            msg = "Error: no filename config option found for"
            msg += " notification plugin " + str(i)
            print(msg)
            LOGGER.error(msg)
            raise
        try:
            enabled = NOTIFICATIONCONFIG.getboolean(i, "enabled")
        except Exception:
            enabled = True

        #if enabled, load the plugin
        if enabled:
            try:
                # 'a' means nothing below, but argument must be non-null
                mod = __import__('notifications.' + filename, fromlist = ['a'])
            except Exception:
                msg = "Error: could not import notification module " + filename
                print(msg)
                LOGGER.error(msg)
                raise

            try:
                notificationclass = get_subclasses(mod, notification.Notification)
                if notificationclass == None:
                    raise AttributeError
            except Exception:
                msg = "Error: could not find a subclass of notification.Notification"
                msg += " in module " + filename
                print(msg)
                LOGGER.error(msg)
                raise
            try:
                reqd = notificationclass.requiredparams
            except Exception:
                reqd = []
            try:
                opt = notificationclass.optionalparams
            except Exception:
                opt = []
            try:
                common = notificationclass.commonParams
            except Exception:
                common = []

            if NOTIFICATIONCONFIG.has_option(i, "async"):
                async = NOTIFICATIONCONFIG.getboolean(i, "async")
            else:
                async = False

            plugindata = {}

            for reqdfield in reqd:
                if NOTIFICATIONCONFIG.has_option(i, reqdfield):
                    plugindata[reqdfield] = NOTIFICATIONCONFIG.get(i, reqdfield)
                else:
                    msg = "Error: Missing required field '" + reqdfield
                    msg += "' for notification plugin " + str(i)
                    msg += "." + os.linesep
                    msg += "Error: This should be found in file: "
                    msg += NOTIFICATIONSCFG
                    print(msg)
                    LOGGER.error(msg)
                    raise MissingField

            for optfield in opt:
                if NOTIFICATIONCONFIG.has_option(i, optfield):
                    plugindata[optfield] = NOTIFICATIONCONFIG.get(i, optfield)

            for commonField in common:
                if NOTIFICATIONCONFIG.has_option("Common", commonField):
                    plugindata[commonField] = NOTIFICATIONCONFIG.get("Common", commonField)

            if NOTIFICATIONCONFIG.has_option(i, "needsinternet"):
                if NOTIFICATIONCONFIG.getboolean(i, "needsinternet"):
                    if not check_conn():
                        msg = "Error: Skipping notification plugin " + str(i)
                        msg += " because no internet connectivity."
                        print(msg)
                        LOGGER.info(msg)
            else:
                instclass = notificationclass(plugindata)
                instclass.async = async

                # check for a sendnotification function
                if callable(getattr(instclass, "sendnotification", None)):
                    notificationplugins.append(instclass)
                    msg = "Success: Loaded notification plugin " + str(i)
                    print(msg)
                    LOGGER.info(msg)
                else:
                    msg = "Error: no callable sendnotification() function for"
                    msg += " notification plugin " + str(i)
                    print(msg)
                    LOGGER.info(msg)

    except Exception as excep:
        msg = "Error: Did not import notification plugin " + str(i) +  + ": " + str(excep)
        print(msg)
        LOGGER.error(msg)
        raise excep

if not os.path.isfile(SETTINGSCFG):
    msg = "Unable to access config file: " + SETTINGSCFG
    print(msg)
    LOGGER.error(msg)
    exit(1)

MAINCONFIG = configparser.SafeConfigParser()
MAINCONFIG.read(SETTINGSCFG)

lastupdated = 0
SAMPLEFREQ = MAINCONFIG.getfloat("Main", "sampleFreq")
OPERATOR = MAINCONFIG.get("Main", "operator")
REDPIN = MAINCONFIG.getint("Main", "redPin")
GREENPIN = MAINCONFIG.getint("Main", "greenPin")
PRINTERRORS = MAINCONFIG.getboolean("Main", "printErrors")
SUCCESSLED = MAINCONFIG.get("Main", "successLED")
FAILLED = MAINCONFIG.get("Main", "failLED")
greenhaslit = False
redhaslit = False

if REDPIN:
    GPIO.setup(REDPIN, GPIO.OUT, initial=GPIO.LOW)
if GREENPIN:
    GPIO.setup(GREENPIN, GPIO.OUT, initial=GPIO.LOW)

# Register the signal handler
signal.signal(signal.SIGINT, interrupt_handler)

print("Success: Setup complete.")
if metadata is not None:
    print("==========================================================")
    print(metadata)
    print("==========================================================")

rightnow = datetime.now()
seconds = float(rightnow.second + (rightnow.microsecond / 1000000))
delay = (60 - seconds)
print("Sampling will start in " + str(int(delay)) + " seconds...")
print("Press Ctrl + C to stop sampling.")
print("==========================================================")
time.sleep(delay)

while True:
    try:
        curtime = time.time()
        sampletime = None
        if (curtime - lastupdated) > SAMPLEFREQ:
            lastupdated = curtime
            data = []
            alreadysentsensoralerts = False
            alreadysentoutputalerts = False
            # Collect the data from each sensor
            sensorsworking = True
            for i in sensorplugins:
                datadict = {}
                if i == gpsplugininstance:
                    val = i.getval()
                    sampletime = datetime.now()
                    if isnan(val[2]): # this means it has no data to upload.
                        continue
                    LOGGER.debug("GPS output %s" % (val,))
                    # handle GPS data
                    datadict["latitude"] = val[0]
                    datadict["longitude"] = val[1]
                    datadict["altitude"] = val[2]
                    datadict["disposition"] = val[3]
                    datadict["exposure"] = val[4]
                    datadict["name"] = i.valname
                    datadict["sensor"] = i.sensorname
                else:
                    sampletime = datetime.now()
                    datadict["value"] = i.getval()
                    # TODO: Ensure this is robust
                    if datadict["value"] is None or isnan(float(datadict["value"])) or datadict["value"] == 0:
                        sensorsworking = False
                    datadict["unit"] = i.valunit
                    datadict["symbol"] = i.valsymbol
                    datadict["name"] = i.valname
                    datadict["sensor"] = i.sensorname
                    datadict["description"] = i.description
                    datadict["readingtype"] = i.readingtype
                data.append(datadict)
            # Record the outcome
            if sensorsworking:
                LOGGER.info("Success: Data obtained from all sensors.")
            else:
                if not alreadysentsensoralerts:
                    for j in notificationplugins:
                        j.sendnotification("alertsensor")
                    alreadysentsensoralerts = True
                if PRINTERRORS:
                    print("Error: Failed to obtain data from all sensors.")
                LOGGER.error("Failed to obtain data from all sensors.")
            # Output data
            try:
                outputsworking = True
                for i in outputplugins:
                    outputsworking = i.outputdata(data, sampletime)
                # Record the outcome
                if outputsworking:
                    LOGGER.info("Success: Data output in all requested formats.")
                    if GREENPIN and (SUCCESSLED == "all" or (SUCCESSLED == "first" and not greenhaslit)):
                        GPIO.output(GREENPIN, GPIO.HIGH)
                        greenhaslit = True
                else:
                    if not alreadysentoutputalerts:
                        for j in notificationplugins:
                            j.sendnotification("alertoutput")
                        alreadysentoutputalerts = True
                    if PRINTERRORS:
                        print("Error: Failed to output in all requested formats.")
                    LOGGER.error("Failed to output in all requested formats.")
                    if REDPIN and (FAILLED in ["all", "constant"] or (FAILLED == "first" and not redhaslit)):
                        GPIO.output(REDPIN, GPIO.HIGH)
                        redhaslit = True
            except KeyboardInterrupt:
                raise
            except Exception as excep:
                LOGGER.error("Exception: %s" % excep)
            else:
                # delay before turning off LED
                time.sleep(1)
                if GREENPIN:
                    GPIO.output(GREENPIN, GPIO.LOW)
                if REDPIN and FAILLED != "constant":
                    GPIO.output(REDPIN, GPIO.LOW)
        try:
            time.sleep(SAMPLEFREQ-(time.time()-curtime)-0.01)
        except KeyboardInterrupt:
            raise
        except Exception:
            pass # fall back on old method...
    except KeyboardInterrupt:
        interrupt_handler()

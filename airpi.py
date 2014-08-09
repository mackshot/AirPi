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
from urllib.request import urlopen
import logging, logging.handlers
from math import isnan
from sensors import sensor
from outputs import output
from notifications import notification

CFGDIR = '/home/pi/AirPi'
SENSORSCFG = os.path.join(CFGDIR, 'sensors.cfg')
OUTPUTSCFG = os.path.join(CFGDIR, 'outputs.cfg')
SETTINGSCFG = os.path.join(CFGDIR, 'settings.cfg')
NOTIFICATIONSCFG = os.path.join(CFGDIR, 'notifications.cfg')

LOG_FILENAME = os.path.join(CFGDIR, 'airpi.log')
# Set up a specific logger with our desired output level
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# create handler and add it to the logger
handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=40960, backupCount=5)
logger.addHandler(handler)
# create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
# Uncomment below for more verbose logging output
#logging.basicConfig(level=logging.DEBUG)

def interrupt_handler(signal, frame):
    """Handle the Ctrl+C KeyboardInterrupt by exiting."""
    if gpsplugininstance:
        gpsplugininstance.stopController()
    GPIO.output(greenpin, GPIO.LOW)
    GPIO.output(redpin, GPIO.LOW)
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

    Check whether there is internet connectivity by trying to connect to a website.

    Returns:
        Boolean True if successfully connects to the site within five seconds.
        Boolean False if fails to connect to the site within five seconds.

    """
    try:
        urlopen("http://www.google.com", timeout=5)
        return True
    except URLError as err:
        pass
    return False

class MissingField(Exception):
    """Exception to be raised when an imported plugin is missing a required field.  """
    pass

if not os.path.isfile(SENSORSCFG):
    msg = "Unable to access config file: " + SENSORSCFG
    print(msg)
    logger.error(msg)
    exit(1)

sensorconfig = configparser.SafeConfigParser()
sensorconfig.read(SENSORSCFG)

sensornames = sensorconfig.sections()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM) #Use BCM GPIO numbers.

sensorplugins = []
gpsplugininstance = None

for i in sensornames:
    try:
        try:
            filename = sensorconfig.get(i, "filename")
        except Exception:
            msg = "Error: no filename config option found for sensor plugin " + str(i)
            print(msg)
            logger.error(msg)
            raise
        try:
            enabled = sensorconfig.getboolean(i, "enabled")
        except Exception:
            enabled = True

        #if enabled, load the plugin
        if enabled:
            try:
                mod = __import__('sensors.' + filename, fromlist=['a']) #Why does this work?
            except Exception:
                msg = "Error: could not import sensor module " + filename
                print(msg)
                logger.error(msg)
                raise

            try:
                sensorclass = get_subclasses(mod, sensor.Sensor)
                if sensorclass == None:
                    raise AttributeError
            except Exception:
                msg = "Error: could not find a subclass of sensor.Sensor in module" + filename
                print(msg)
                logger.error(msg)
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

            for requiredfield in reqd:
                if sensorconfig.has_option(i, requiredfield):
                    plugindata[requiredfield] = sensorconfig.get(i, requiredfield)
                else:
                    msg = "Error: Missing required field '" + requiredfield
                    msg += "' for sensor plugin " + i + "." + os.linesep
                    msg += "Error: This should be found in file: " + SENSORSCFG
                    print(msg)
                    logger.error(msg)
                    raise MissingField
            for optionalfield in opt:
                if sensorconfig.has_option(i, optionalfield):
                    plugindata[optionalfield] = sensorconfig.get(i, optionalfield)
            instclass = sensorclass(plugindata)
            # check for a getval
            if callable(getattr(instclass, "getval", None)):
                sensorplugins.append(instclass)
                # store sensorplugins array length for GPS plugin
                if i == "GPS":
                    gpsplugininstance = instclass
                msg = "Success: Loaded sensor plugin " + str(i)
                print(msg)
                logger.info(msg)
            else:
                msg = "Success: Loaded support plugin " + str(i)
                print(msg)
                logger.info(msg)
    except Exception as e: #add specific exception for missing module
        msg = "Error: Did not import sensor plugin " + str(i) + ": " + str(e)
        print(msg)
        logger.error(msg)
        raise e



if not os.path.isfile(OUTPUTSCFG):
    msg = "Unable to access config file: " + OUTPUTSCFG
    print(msg)
    logger.error(msg)
    exit(1)

outputconfig = configparser.SafeConfigParser()
outputconfig.read(OUTPUTSCFG)

outputnames = outputconfig.sections()

outputplugins = []

metadata = None

for i in outputnames:
    try:
        try:
            filename = outputconfig.get(i, "filename")
        except Exception:
            msg = "Error: no filename config option found for output plugin " + str(i)
            print(msg)
            logger.error(msg)
            raise
        try:
            enabled = outputconfig.getboolean(i, "enabled")
        except Exception:
            enabled = True

        #if enabled, load the plugin
        if enabled:
            try:
                mod = __import__('outputs.' + filename, fromlist=['a']) #Why does this work?
            except Exception:
                msg = "Error: could not import output module " + filename
                print(msg)
                logger.error(msg)
                raise

            try:
                outputclass = get_subclasses(mod, output.Output)
                if outputclass == None:
                    raise AttributeError
            except Exception:
                msg = "Error: could not find a subclass of output.Output in module " + filename
                print(msg)
                logger.error(msg)
                raise

            try:
                reqd = outputclass.requiredparams
            except Exception:
                reqd = []
            try:
                opt = outputclass.optionalparams
            except Exception:
                opt = []
            if outputconfig.has_option(i, "async"):
                async = outputconfig.getboolean(i, "async")
            else:
                async = False

            plugindata = {}
            for requiredfield in reqd:
                if outputconfig.has_option(i, requiredfield):
                    plugindata[requiredfield] = outputconfig.get(i, requiredfield)
                else:
                    msg = "Error: Missing required field '" + requiredfield
                    msg += "' for output plugin " + str(i) + "." + os.linesep
                    msg += "Error: This should be found in file: " + OUTPUTSCFG
                    print(msg)
                    logger.error(msg)
                    raise MissingField
            for optionalfield in opt:
                if outputconfig.has_option(i, optionalfield):
                    plugindata[optionalfield] = outputconfig.get(i, optionalfield)

            if outputconfig.has_option(i, "needsinternet") and outputconfig.getboolean(i, "needsinternet") and not check_conn():
                msg = "Error: Skipping output plugin " + i + " because no internet connectivity."
                print(msg)
                logger.info(msg)
            else:
                instclass = outputclass(plugindata)
                instclass.async = async

                # check for a outputdata() function
                if callable(getattr(instclass, "outputdata", None)):
                    outputplugins.append(instclass)
                    msg = "Success: Loaded output plugin " + str(i)
                    print(msg)
                    logger.info(msg)
                else:
                    msg = "Success: Loaded support plugin " + str(i)
                    print(msg)
                    logger.info(msg)

                # Check for an outputmetadata function
                if outputconfig.has_option(i, "metadatareqd") and outputconfig.getboolean(i, "metadatareqd"):
                    if callable(getattr(instclass, "outputmetadata", None)):
                        # We'll printthis later on
                        metadata = instclass.outputmetadata()

    except Exception as e: #add specific exception for missing module
        msg = "Error: Did not import output plugin " + str(i)
        print(msg)
        logger.error(msg)
        raise e

if not outputplugins:
    msg = "There are no output plugins enabled! Please enable at least one in " + OUTPUTSCFG + " and try again."
    print(msg)
    logger.error(msg)
    sys.exit(1)

if not os.path.isfile(NOTIFICATIONSCFG):
    msg = "Unable to access config file: " + NOTIFICATIONSCFG
    print(msg)
    logger.error(msg)
    exit(1)

notificationconfig = configparser.SafeConfigParser()
notificationconfig.read(NOTIFICATIONSCFG)

notificationnames = notificationconfig.sections()
notificationnames.remove("Common")

notificationplugins = []

for i in notificationnames:
    try:
        try:
            filename = notificationconfig.get(i, "filename")
        except Exception:
            msg = "Error: no filename config option found for notification plugin " + str(i)
            print(msg)
            logger.error(msg)
            raise
        try:
            enabled = notificationconfig.getboolean(i, "enabled")
        except Exception:
            enabled = True

        #if enabled, load the plugin
        if enabled:
            try:
                mod = __import__('notifications.' + filename, fromlist = ['a']) #Why does this work?
            except Exception:
                msg = "Error: could not import notification module " + filename
                print(msg)
                logger.error(msg)
                raise

            try:
                notificationclass = get_subclasses(mod, notification.Notification)
                if notificationclass == None:
                    raise AttributeError
            except Exception:
                msg = "Error: could not find a subclass of notification.Notification in module " + filename
                print(msg)
                logger.error(msg)
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

            if notificationconfig.has_option(i, "async"):
                async = notificationconfig.getboolean(i, "async")
            else:
                async = False

            plugindata = {}

            for requiredfield in reqd:
                if notificationconfig.has_option(i, requiredfield):
                    plugindata[requiredfield] = notificationconfig.get(i, requiredfield)
                else:
                    msg = "Error: Missing required field '" + requiredfield
                    msg += "' for notification plugin " + str(i) + "." + os.linesep
                    msg += "Error: This should be found in file: " + NOTIFICATIONSCFG
                    print(msg)
                    logger.error(msg)
                    raise MissingField

            for optionalfield in opt:
                if notificationconfig.has_option(i, optionalfield):
                    plugindata[optionalfield] = notificationconfig.get(i, optionalfield)

            for commonField in common:
                if notificationconfig.has_option("Common", commonField):
                    plugindata[commonField] = notificationconfig.get("Common", commonField)

            if notificationconfig.has_option(i, "needsinternet") and notificationconfig.getboolean(i, "needsinternet") and not check_conn():
                msg = "Error: Skipping notification plugin " + str(i) + " because no internet connectivity."
                print(msg)
                logger.info(msg)
            else:
                instclass = notificationclass(plugindata)
                instclass.async = async

                # check for a sendnotification function
                if callable(getattr(instclass, "sendnotification", None)):
                    notificationplugins.append(instclass)
                    msg = "Success: Loaded notification plugin " + str(i)
                    print(msg)
                    logger.info(msg)
                else:
                    msg = "Error: no callable sendnotification() function for notification plugin " + str(i)
                    print(msg)
                    logger.info(msg)

    except Exception as e:
        msg = "Error: Did not import notification plugin " + str(i)
        print(msg)
        logger.error(msg)
        raise e

if not os.path.isfile(SETTINGSCFG):
    msg = "Unable to access config file: " + SETTINGSCFG
    print(msg)
    logger.error(msg)
    exit(1)

mainconfig = configparser.SafeConfigParser()
mainconfig.read(SETTINGSCFG)

lastupdated = 0
samplefreq = mainconfig.getfloat("Main", "sampleFreq")
operator = mainconfig.get("Main", "operator")
redpin = mainconfig.getint("Main", "redpin")
greenpin = mainconfig.getint("Main", "greenpin")
printerrors = mainconfig.getboolean("Main", "printerrors")
successled = mainconfig.get("Main", "successled")
failled = mainconfig.get("Main", "failled")
greenhaslit = False
redhaslit = False

if redpin:
    GPIO.setup(redpin, GPIO.OUT, initial=GPIO.LOW)
if greenpin:
    GPIO.setup(greenpin, GPIO.OUT, initial=GPIO.LOW)

print("Success: Setup complete - starting to sample...")
print("Press Ctrl + C to stop sampling.")
print("==========================================================")
if metadata is not None:
    print(metadata)
    print("==========================================================")

# Register the signal handler
signal.signal(signal.SIGINT, interrupt_handler)


while True:
    try:
        curTime = time.time()
        if (curTime - lastupdated) > samplefreq:
            lastupdated = curTime
            data = []
            alreadysentsensoralerts = False
            #Collect the data from each sensor
            sensorsworking = True
            for i in sensorplugins:
                datadict = {}
                if i == gpsplugininstance:
                    val = i.getval()
                    if isnan(val[2]): # this means it has no data to upload.
                        continue
                    logger.debug("GPS output %s" % (val,))
                    # handle GPS data
                    datadict["latitude"] = val[0]
                    datadict["longitude"] = val[1]
                    datadict["altitude"] = val[2]
                    datadict["disposition"] = val[3]
                    datadict["exposure"] = val[4]
                    datadict["name"] = i.valname
                    datadict["sensor"] = i.sensorname
                else:
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
            if sensorsworking:
                logger.info("Success: Data obtained from all sensors.")
            else:
                if not alreadysentsensoralerts:
                    for j in notificationplugins:
                        j.sendnotification("alertsensor")
                    alreadysentsensoralerts = True
                if printerrors:
                    print("Error: Failed to obtain data from all sensors.")
                logger.error("Failed to obtain data from all sensors.")
            try:
                outputsworking = True
                for i in outputplugins:
                    outputsworking = i.outputdata(data)
                if outputsworking:
                    logger.info("Success: Data output in all requested formats.")
                    if greenpin and (successled == "all" or (successled == "first" and not greenhaslit)):
                        GPIO.output(greenpin, GPIO.HIGH)
                        greenhaslit = True
                else:
                    if not alreadysentoutputalerts:
                        for j in notificationplugins:
                            j.sendnotification("alertoutput")
                        alreadysentoutputalerts = True
                    if printerrors:
                        print("Error: Failed to output in all requested formats.")
                    logger.error("Failed to output in all requested formats.")
                    if redpin and (failled in ["all", "constant"] or (failled == "first" and not redhaslit)):
                        GPIO.output(redpin, GPIO.HIGH)
                        redhaslit = True
            except KeyboardInterrupt:
                raise
            except Exception as e:
                logger.error("Exception: %s" % e)
            else:
                # delay before turning off LED
                time.sleep(1)
                if greenpin:
                    GPIO.output(greenpin, GPIO.LOW)
                if redpin and failled != "constant":
                    GPIO.output(redpin, GPIO.LOW)
        try:
            time.sleep(samplefreq-(time.time()-curTime)-0.01)
        except KeyboardInterrupt:
            raise
        except Exception:
            pass # fall back on old method...
    except KeyboardInterrupt:
        interrupt_handler()
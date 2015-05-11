"""Generic AirPi plugin description (abstract) for sub-classing.

A generic description of an AirPi plugin, which can then be sub-classed
for more specific purposes. This is an abstract base class (ABC) and so cannot
be instantiated directly.

"""
from abc import ABCMeta, abstractmethod
import socket
import ConfigParser
import os
import urllib2

class Plugin(object):
    """Generic AirPi plugin description (abstract) for sub-classing.

    A generic description of an AirPi plugin, which can then be sub-classed
    for more specific purposes. This is an abstract base class (ABC) and so cannot
    be instantiated directly.

    """

    __metaclass__ = ABCMeta
    requiredGenericParams = None
    optionalGenericParams = None
    requiredSpecificParams = None
    optionalSpecificParams = None
    commonParams = None

    def __init__(self, config, purpose):
        self.name = type(self).__name__
        self.purpose = purpose
        #TODO: Is self.async really required?
        self.async = False
        self.params = {}
        if self.setallparams(config):
            if (self.params["target"] == "internet") and not self.check_conn():
                msg = "Skipping " + self.purpose + " plugin " + self.name
                msg += " because no internet connectivity."
                #msg = format_msg(msg, 'error')
                print(msg)
                #logthis("info", msg)
                raise NoInternetConnection
        else:
            msg = "Failed to set parameters for " + self.purpose + " plugin " + self.name
            print(msg)
            #logthis("error", msg)
        if self.params["calibration"]:
            import sys
            sys.path.append(sys.path[0] + '/supports')
            from supports import calibration
            self.cal = calibration.Calibration.sharedClass
 
    def setallparams(self, config):
        """
 
        Check that 'params' used to init the object contains the required
        parameters; raise an error if not. Then check whether it contains
        any of the optional parameters; set them to False if not.
        This is done for both the 'generic' parameters which apply to all
        subclasses of this Plugin object, and for 'specific' parameters
        which are defined for individual subclasses.

        """
        if self.name in config.sections():
            self.extractparams(config, self.requiredGenericParams, "required")
            self.extractparams(config, self.requiredSpecificParams, "required")
            self.extractparams(config, self.optionalGenericParams, "optional")
            self.extractparams(config, self.optionalSpecificParams, "optional")
            return True
        else:
            msg = "Missing config section for " + self.purpose + " plugin " + self.name + "."
            #msg = format_msg(msg, 'error')
            print(msg)
            raise MissingSection
        return False

    def extractparams(self, config, expected, kind):
        """ Extract individual parameters from a set.

        Pull out individual parameters from a set (dict), and assess whether
        the absence of an expected parameter is a major problem or not.

        Args:
            config: ConfigParser object containing the defined parameters.
            expected: Dict containing the expected parameters.
            kind: The kind of parameter, i.e. required or optional.

        """
        if expected is not None:
            extracted = {}
            for param in expected:
                if config.has_option(self.name, param):
                    extracted[param] = self.sanitiseparam(config.get(self.name, param))
                else:
                    if kind == "required":
                        msg = "Missing required parameter '" + param
                        msg += "' for plugin " + self.name + "."
                        print(msg)
                        msg += "This should be found in the relevant .cfg file."
                        #msg = format_msg(msg, 'error')
                        print(msg)
                        raise MissingParameter 
                    else:
                        msg = "Missing optional parameter '" + param 
                        msg += "' for plugin " + self.name + ". Setting to False."
                        #msg = format_msg(msg, 'info')
                        #logthis(msg)
                        extracted[param] = False
            self.params.update(extracted)

    @staticmethod
    def sanitiseparam(value):
        """ Convert values to bool if possible.

        Convert any applicable values found in a .cfg file to the appropriate
        boolean, if possible. Consult the code to see exactly what is
        converted.

        Always test for bool first: http://www.peterbe.com/plog/bool-is-int

        Args:
            value: The value to be converted.

        Returns:
            The value as a boolean.

        """
        if isinstance(value, bool):
            return value
        if value.lower() in ["on", "yes", "true", "1"]:
            return True
        if value.lower() in ["off", "no", "false", "0"]:
            return False
        return value

    @staticmethod
    def check_conn():
        """Check internet connectivity.

        Check for internet connectivity by trying to connect to a website.

        Returns:
            boolean True if successfully connects to the site within five
                    seconds.
            boolean False if fails to connect to the site within five
                    seconds.

        """
        try:
            urllib2.urlopen("http://www.google.com", timeout=5)
            return True
        except urllib2.URLError:
            pass
        return False

    @staticmethod
    def gethostname():
        """Get current hostname.

        Get the current hostname of the Raspberry Pi.

        Returns:
            string The hostname.

        """
        if socket.gethostname().find('.') >= 0:
            host = socket.gethostname()
        else:
            host = socket.gethostbyaddr(socket.gethostname())[0]
        return host

    def getname(self):
        """Get Class name.

        Get the name of the class. Lots of Classes inherit from this class,
        so the name varies depending on which one we're looking at.

        Returns:
            string The class name.

        """
        return self.__class__.__name__

class MissingParameter(Exception):
    """Exception to raise when the outputs.cfg file is missing a required
    parameter.

    """
    pass

class MissingSection(Exception):
    """ Exception to raise when there is no section for the plugin in
    the outputs.cfg config file.

    """
    pass

class NoInternetConnection(Exception):
    """ Exceeption to raise when there is no internet connectivity.

    """
    pass

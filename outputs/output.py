"""Generic Output plugin description (abstract) for sub-classing.

A generic description of an Output plugin, which can then be sub-classed
for specific Outputs. This is an abstract base class (ABC) and so cannot
be instantiated directly.

"""
from abc import ABCMeta, abstractmethod
from plugin import Plugin

class Output(Plugin):
    """Generic Output plugin description (abstract) for sub-classing.

    A generic description of an Output plugin, which can then be sub-classed
    for specific Outputs. This is an abstract base class (ABC) and so cannot
    be instantiated directly.

    """

    requiredGenericParams = ["target"]
    optionalGenericParams = ["calibration", "metadata", "limits"]

    def __init__(self, config):
        super(Output, self).__init__(config, "outputs")

    @abstractmethod
    def output_data(self):
        """Output data.

        Output data in the format stipulated by this plugin.
        Even if it is not appropriate for the plugin to output data
        (e.g. for support plugins), this method is required because
        airpi.py looks for it in when setting up plugins; this is why it
        is abstract.

        The standard method signature would be:
        output_data(self, data, sampletime)
        where...
        - 'data' is a dict containing the data to be output, usually
           called 'datapoints'.
        - 'sampletime' is a datetime representing the time the sample
           was taken.

        In situations where the sub-class defines a support plugin (e.g.
        "calibration") the sub-class may not actually be able/designed
        to ouptput data; in such circumstances the method should just
        return True. In those cases, the method signature can have a
        single 'self' argument as shown above.

        See the docstrings for individual methods within sub-classes for
        more detail on specific cases.

        Args:
            self: self.

        """
        pass

    def output_metadata(self, metadata = None):
        """Output metadata.

        Output metadata in the format stipulated by this plugin.
        Even if it is not appropriate for the plugin to output metadata
        (e.g. for support plugins), this method is required because
        airpi.py looks for it in when setting up plugins; this is why it
        is abstract.

        In situations where the sub-class defines a support plugin (e.g.
        "calibration") the sub-class may not actually be able/designed
        to ouptput data; in such circumstances the method should just
        return True. In those cases, the method signature can have a
        single 'self' argument as shown above;  the 'metadata' argument 
        is never used.

        See the docstrings for individual methods within sub-classes for
        more detail on specific cases.

        Args:
            self: self.
            metadata: Dict containing the metadata to be output.

        """
        return True

"""Generic Support plugin description (abstract) for sub-classing.

A generic description of a Support plugin, which can then be sub-classed
for specific Supports. This is an abstract base class (ABC) and so cannot
be instantiated directly.

"""
from abc import ABCMeta, abstractmethod
from plugin import Plugin

class Support(Plugin):
    """Generic Support plugin description (abstract) for sub-classing.

    A generic description of a Support plugin, which can then be sub-classed
    for specific Supports. This is an abstract base class (ABC) and so cannot
    be instantiated directly.
    Note that Support plugins do not currently have any generic params,
    nor do they check for internet connectivity.

    """

    __metaclass__ = ABCMeta

    def __init__(self, config):
        super(Support, self).__init__(config, "supports")

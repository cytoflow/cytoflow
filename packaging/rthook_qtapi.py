import os

os.environ["QT_API"] = "pyqt5"

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt'

os.environ["ETS_DEBUG"] = "1"


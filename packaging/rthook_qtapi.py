import os, sys

os.environ["QT_API"] = "pyqt5"

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt'


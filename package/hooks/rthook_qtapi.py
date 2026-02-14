import os, sys

os.environ["QT_API"] = "pyside6"

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt'


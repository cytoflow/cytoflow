import os, sys

os.environ["QT_API"] = "pyqt5"

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt'

pyqt_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt')
os.environ['QT_PLUGIN_PATH'] = os.path.join(pyqt_path, 'plugins')
os.environ['QML2_IMPORT_PATH'] = os.path.join(pyqt_path, 'qml')

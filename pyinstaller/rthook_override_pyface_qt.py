import sys

import pyinstaller.override_pyface_qt
import pyinstaller.override_pyface_qt.QtCore
import pyinstaller.override_pyface_qt.QtGui

sys.modules['pyface.qt'] = pyinstaller.override_pyface_qt
sys.modules['pyface.qt.QtCore'] = pyinstaller.override_pyface_qt.QtCore
sys.modules['pyface.qt.QtGui'] = pyinstaller.override_pyface_qt.QtGui

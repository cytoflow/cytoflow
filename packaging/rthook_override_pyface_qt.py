import sys

import packaging.qt
import packaging.qt.QtCore
import packaging.qt.QtGui
import packaging.qt.QtSvg

sys.modules['pyface.qt'] = packaging.qt
sys.modules['pyface.qt.QtCore'] = packaging.qt.QtCore
sys.modules['pyface.qt.QtGui'] = packaging.qt.QtGui
sys.modules['pyface.qt.QtSvg'] = packaging.qt.QtSvg

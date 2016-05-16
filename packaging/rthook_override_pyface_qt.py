import sys

import dist.qt
import dist.qt.QtCore
import dist.qt.QtGui

sys.modules['pyface.qt'] = dist.qt
sys.modules['pyface.qt.QtCore'] = dist.qt.QtCore
sys.modules['pyface.qt.QtGui'] = dist.qt.QtGui

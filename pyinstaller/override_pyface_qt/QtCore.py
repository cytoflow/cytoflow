from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtCore import *

    from PyQt4.QtCore import pyqtProperty as Property
    from PyQt4.QtCore import pyqtSignal as Signal
    from PyQt4.QtCore import pyqtSlot as Slot
    from PyQt4.QtCore import QCoreApplication
    #from PyQt4.Qt import Qt

    print "good import 1"

    __version__ = QT_VERSION_STR
    __version_info__ = tuple(map(int, QT_VERSION_STR.split('.')))

else:
    try:
        from PySide import __version__, __version_info__
    except ImportError:
        pass
    from PySide.QtCore import *

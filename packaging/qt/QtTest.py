from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtTest import *

elif qt_api == 'pyqt5':
    from PyQt5.QtTest import *

elif qt_api == 'pyside2':
    from PySide2.QtTest import *

else:
    from PySide.QtTest import *

from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtNetwork import *

elif qt_api == 'pyqt5':
    from PyQt5.QtNetwork import *

elif qt_api == 'pyside2':
    from PySide2.QtNetwork import *

else:
    from PySide.QtNetwork import *

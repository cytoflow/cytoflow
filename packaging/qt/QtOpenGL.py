from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtOpenGL import *

elif qt_api == 'pyqt5':
    from PyQt5.QtOpenGL import *

elif qt_api == 'pyside2':
    from PySide2.QtOpenGL import *

else:
    from PySide.QtOpenGL import *

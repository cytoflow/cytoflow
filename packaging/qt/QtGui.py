from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtGui import *
    
else:
    from PySide.QtGui import *

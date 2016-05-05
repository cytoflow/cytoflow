from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtGui import *

    print "good import 2"
    
else:
    from PySide.QtGui import *

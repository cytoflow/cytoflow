from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.Qt import QKeySequence, QTextCursor
    from PyQt4.QtGui import *

elif qt_api == 'pyqt5':
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtPrintSupport import *
    from PyQt5.QtCore import (
        QAbstractProxyModel, QItemSelection, QItemSelectionModel,
        QItemSelectionRange, QSortFilterProxyModel, QStringListModel
    )

elif qt_api == 'pyside2':
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
    from PySide2.QtPrintSupport import *
    from PySide2.QtCore import (
        QAbstractProxyModel, QItemSelection, QItemSelectionModel,
        QItemSelectionRange, QSortFilterProxyModel
    )

else:
    from PySide.QtGui import *

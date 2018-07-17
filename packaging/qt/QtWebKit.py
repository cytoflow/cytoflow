from . import qt_api

if qt_api == 'pyqt':
    from PyQt4.QtWebKit import *

elif qt_api == 'pyqt5':
    #from PyQt5.QtWebKit import *
    #from PyQt5.QtWebKitWidgets import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtWebEngine import *
    from PyQt5.QtWebEngineWidgets import (
        QWebEngineHistory as QWebHistory,
        QWebEngineHistoryItem as QWebHistoryItem,
        QWebEnginePage as QWebPage,
        QWebEngineView as QWebView,
    )

elif qt_api == 'pyside2':
    from PyQt5.QtWidgets import *
    # WebKit is currently in flux in PySide2
    try:
        from PySide2.QtWebEngineWidgets import (
            QWebEngineHistory as QWebHistory,
            QWebEngineHistoryItem as QWebHistoryItem,
            QWebEnginePage as QWebPage,
            QWebEngineView as QWebView
        )
    except ImportError:
        from PySide2.QtWebKitWidgets import *

else:
    from PySide.QtWebKit import *

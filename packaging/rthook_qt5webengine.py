import os
import sys

if sys.platform == 'darwin' or sys.platform.startswith('linux'):
    os.environ['QTWEBENGINEPROCESS_PATH'] = os.path.normpath(os.path.join(
        sys._MEIPASS, 'PyQt5', 'Qt', 'libexec', 'QtWebEngineProcess'
    ))
    

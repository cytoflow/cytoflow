import os, sys

if sys.platform == 'darwin' or sys.platform.startswith('linux'):
    os.environ['QTWEBENGINEPROCESS_PATH'] = os.path.normpath(os.path.join(
        sys._MEIPASS, 'PyQt5', 'Qt', 'libexec', 'QtWebEngineProcess'
    ))

    if not os.path.exists(os.path.normpath(os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'lib'))):
        os.symlink(sys._MEIPASS + '/', os.path.normpath(os.path.join(
            sys._MEIPASS, 'PyQt5', 'Qt', 'lib')))
    

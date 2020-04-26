import os
import sys

# if sys.platform == 'darwin' or sys.platform.startswith('linux'):
if sys.platform.startswith('linux'):
    os.environ['QTWEBENGINEPROCESS_PATH'] = os.path.normpath(os.path.join(
        sys._MEIPASS, 'PyQt5', 'Qt', 'libexec', 'QtWebEngineProcess'
    ))
    
    qt_conf_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'libexec', 'qt.conf')
    qt_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt')
    with open(qt_conf_path, 'w') as qt_conf:
        qt_conf.write('[Paths]\nPrefix = {}\n'.format(qt_path))
    
    if not os.path.exists(os.path.normpath(os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'lib'))):
        os.symlink(sys._MEIPASS + '/', os.path.normpath(os.path.join(
            sys._MEIPASS, 'PyQt5', 'Qt', 'lib')))

elif sys.platform.startswith('win'):

    qt_conf_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'bin', 'qt.conf')
    qt_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt')

    # QT's init file format requires front-slashes even on windows
    if sys.platform.startswith('win'):
       qt_path = qt_path.replace("\\", '/')

    with open(qt_conf_path, 'w') as qt_conf:
        qt_conf.write('[Paths]\nPrefix = {}\n'.format(qt_path))
        
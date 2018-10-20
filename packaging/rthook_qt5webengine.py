#-----------------------------------------------------------------------------
# Copyright (c) 2015-2018, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

import os
import sys
import stat
import shutil

# See ``pyi_rth_qt5.py`: use a "standard" PyQt5 layout.
if sys.platform == 'darwin':
    os.environ['QTWEBENGINEPROCESS_PATH'] = os.path.normpath(os.path.join(
        sys._MEIPASS, '..', 'Resources', 'PyQt5', 'Qt', 'lib',
        'QtWebEngineCore.framework', 'Helpers'
    ))

elif sys.platform.startswith('linux'):
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
    

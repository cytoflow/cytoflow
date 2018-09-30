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
        sys._MEIPASS, 'PyQt5', 'Qt', 'libexec'
    ))
    
    if not os.path.exists(os.path.normpath(os.path.join(sys._MEIPASS, 'PyQt5', 'Qt', 'lib'))):
        os.symlink(sys._MEIPASS + '/', os.path.normpath(os.path.join(
            sys._MEIPASS, 'PyQt5', 'Qt', 'lib')))
# 
#     if os.path.exists(os.path.normpath(os.path.join(sys._MEIPASS, 'PyQt5', 'cf_test'))):
#         shutil.rmtree(os.path.normpath(os.path.join(sys._MEIPASS, 'PyQt5', 'cf_test')))
        
#     os.chmod(os.path.join(sys._MEIPASS, 'PyQt5', 'Qt'), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
#     for dirpath, dirnames, filenames in os.walk(os.path.join(sys._MEIPASS, 'PyQt5', 'Qt')):
#         for dname in dirnames:
#             os.chmod(os.path.join(dirpath, dname), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)


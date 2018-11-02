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
import tempfile
import pathlib

#qrc_path = os.path.join(sys._MEIPASS, 'qt_conf.qrc')
#qrc_py_path = os.path.join(sys._MEIPASS, 'qt_conf.py')
#qt_conf_path = os.path.join(sys._MEIPASS, 'qt.conf')

qt_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt')

# QT's init file format requires front-slashes even on windows
if sys.platform.startswith('win'):
   qt_path = qt_path.replace("\\", '/')
    
qt_conf_handle, qt_conf_filename = tempfile.mkstemp(dir = sys._MEIPASS, 
                                                    text = True)
os.write(qt_conf_handle, '[Paths]\nPrefix = {}\n'.format(qt_path).encode('utf-8'))
os.close(qt_conf_handle)

qrc_handle, qrc_filename = tempfile.mkstemp(dir = sys._MEIPASS,
                                            text = True)
os.write(qrc_handle, """
<!DOCTYPE RCC>
<RCC version="1.0">
<qresource prefix="/qt/etc">
    <file alias="qt.conf">{}</file>
</qresource>
</RCC> """.format(pathlib.Path(qt_conf_filename).name).encode('utf-8'))

os.close(qrc_handle)
        
import PyQt5.pyrcc_main

# this is a little unsafe, but I'm not sure what else to do.
qrc_mod_handle, qrc_mod_filename = tempfile.mkstemp(dir = sys._MEIPASS)
os.close(qrc_mod_handle)
os.unlink(qrc_mod_filename)
PyQt5.pyrcc_main.processResourceFile([qrc_filename], qrc_mod_filename, False)

qrc_mod_handle = open(qrc_mod_filename, 'r')
contents = qrc_mod_handle.read()
exec(contents)
qrc_mod_handle.close()

os.unlink(qrc_mod_filename)
os.unlink(qrc_filename)
os.unlink(qt_conf_filename)


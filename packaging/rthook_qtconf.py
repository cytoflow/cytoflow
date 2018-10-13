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

qrc_path = os.path.join(sys._MEIPASS, 'qt_conf.qrc')
qrc_py_path = os.path.join(sys._MEIPASS, 'qt_conf.py')
qt_conf_path = os.path.join(sys._MEIPASS, 'qt.conf')
qt_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt')

with open(qt_conf_path, 'w') as qt_conf:
    qt_conf.write('[Paths]\nPrefix = {}\n'.format(qt_path))

with open(qrc_path, 'w') as qrc:
    qrc.write("""
<!DOCTYPE RCC>
<RCC version="1.0">
<qresource prefix="/qt/etc">
    <file alias="qt.conf">qt.conf</file>
</qresource>
</RCC> """)

import PyQt5.pyrcc_main
PyQt5.pyrcc_main.processResourceFile([qrc_path], qrc_py_path, False)

import qt_conf


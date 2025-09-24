import sys, os, re, weakref, glob, logging
from PyInstaller.compat import is_win, is_darwin, is_linux
from PyInstaller.utils.hooks import copy_metadata

a = Analysis(['../cytoflowgui/run.py'],
             pathex=['cytoflowgui/'],
             binaries=None,
             datas=[('../cytoflowgui/preferences.ini', 'cytoflowgui'),
                    ('../cytoflowgui/images', '.'),
                    ('../cytoflowgui/op_plugins/images', 'cytoflowgui/op_plugins/images'),
                    ('../cytoflowgui/view_plugins/images', 'cytoflowgui/view_plugins/images'),
                    ('../cytoflowgui/editors/images', 'cytoflowgui/editors/images'),
                    ('../cytoflowgui/help', 'cytoflowgui/help'),
                    ('../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs', '.'),
                    ('icon.png', '.'),
                    ('cytoflow.desktop', '.'),
                    ('set_launcher_icon', '.')] 
                      + copy_metadata('cytoflow', recursive=True),
             hookspath=['package/hooks'],
             runtime_hooks=['package/hooks/rthook_qtapi.py',],
             excludes=[
             	# Unused modules
                'IPython', 'docutils', 'ipykernel', 'jupyter_client', 
                'prompt_toolkit', 'sphinx', 'tkinter', 'tornado',
                'zmq'
                
             	# Unused Qt5 libraries
                'PyQt5.QtBluetooth', 'PyQt5.QtDesigner',
                'PyQt5.QtHelp', 'PyQt5.QtLocation',
                'PyQt5.QtMultimediaWidgets', 'PyQt5.QtNfc', 
                'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets',
                'PyQt5.QtSensors', 'PyQt5.QtSerialPort', 'PyQt5.QtSql',
                'PyQt5.QtTest', 'PyQt5.QtWebSockets', 'PyQt5.QtXml',
                'PyQt5.QtXmlPatterns',
                ],
                
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None)
             
# remove a few libraries that cause crashes if we don't use the system
# versions

remove_strs = ["glib", "gobject", "gthread", "libX", "libICE", "libdrm", "terminfo"]

# on linux, Anaconda version of fontconfig looks for the config bundled with
# Anaconda instead of the system config.  this breaks the fonts when you
# run on a system that you didn't build on

remove_strs.append('libfontconfig')
remove_strs.append('libuuid')

lol = [ [x for x in a.binaries if x[0].find(y) >= 0] for y in remove_strs]
remove_binaries = [item for sublist in lol for item in sublist]
logging.info("Removing binaries: {}".format(remove_binaries))

a.binaries = list(set(a.binaries) - set(remove_binaries))

# the following remove "cruft" files from the install
# this is important because they make the windows uninstaller REALLY slow

# the pytz zoneinfo files aren't used afaict
remove_strs = ['pytz/zoneinfo']

# setuptools cruft
# remove_strs.append('dist-info')

# sphinx cruft
remove_strs.append('.doctrees')

# matplotlib cruft
remove_strs.append('mpl-data/sample_data')

# sklearn cruft
remove_strs.append('sklearn/datasets')

# unused (??) Qt translations
# remove_strs.append('Qt5/translations')

lol = [ [x for x in a.datas if x[0].find(y) >= 0] for y in remove_strs]
remove_datas = [item for sublist in lol for item in sublist]
logging.info("Removing datas: {}".format(remove_datas))

a.datas = list(set(a.datas) - set(remove_datas))

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz,
          a.scripts,
          [],
          #[('u', None, 'OPTION'), ('v', None, 'OPTION')],
          exclude_binaries=True,
          name='cytoflow',
          debug=False,
          strip=False,
          upx=False,
          console=False,
          bootloader_ignore_signals=False,
          codesign_identity = '###REPLACEME###',
          entitlements_file = 'package/entitlements.plist',
          icon='icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='cytoflow',
               icon='icon.ico')

if sys.platform == 'darwin':
   app = BUNDLE(coll,
                name = "Cytoflow.app",
                icon = "icon.icns",
                bundle_identifier=None)



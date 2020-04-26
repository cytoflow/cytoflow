import sys

a = Analysis(['../cytoflowgui/run.py'],
             pathex=['cytoflowgui/'],
             binaries=None,
             datas=[('../cytoflowgui/preferences.ini', 'cytoflowgui'),
                    ('../cytoflowgui/images', '.'),
                    ('../cytoflowgui/op_plugins/images', 'cytoflowgui/op_plugins/images'),
                    ('../cytoflowgui/view_plugins/images', 'cytoflowgui/view_plugins/images'),
                    ('../cytoflowgui/help', 'cytoflowgui/help')],
             hiddenimports = [
                 'matplotlib.backends.backend_qt5agg',
                 'matplotlib_backend',
                 'pkg_resources.py2_warn',  # fix for setuptools >= 45.0
             ],
             hookspath=['packaging'],
             runtime_hooks=['packaging/rthook_qtapi.py',
                            'packaging/rthook_seaborn.py',
                            'packaging/rthook_qtconf.py'],
             excludes=['gi.repository.Gio', 'gi.repository.GModule',
                       'gi.repository.GObject', 'gi.repository.Gtk',
                       'gi.repository.Gdk', 'gi.repository.Atk',
                       'gi.repository.cairo', 'gi.repository.GLib',
                       'gobject', 'Tkinter', 'FixTk', '_tkinter',
                       'PySide', 'PySide.QtCore', 'PySide.QtGui',
                       'PySide.QtNetwork', 'PySide.QtSvg', 'PyQt4',
                       'PyQt5.QtBluetooth', 'PyQt5.QtDesigner',
                       'PyQt5.QtHelp', 'PyQt5.QtLocation',
                       'PyQt5.QtMultimediaWidgets', 'PyQt5.QtNfc', 
                       'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets',
                       'PyQt5.QtSensors', 'PyQt5.QtSerialPort', 'PyQt5.QtSql',
                       'PyQt5.QtTest', 'PyQt5.QtWebSockets', 'PyQt5.QtXml',
                       'PyQt5.QtXmlPatterns',
                       'pyface.wx', 'traitsui.wx', 'IPython','wx',
                       'gtk', 'gi', 'sphinx', 'twisted', 'zope',
                       'jinja2', 'httplib2', '_mysql',
                       'sqlalchemy', 'zmq'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None)

# remove a few libraries that cause crashes if we don't use the system
# versions

remove_strs = ["glib", "gobject", "gthread", "libX", "libICE", "libdrm", 
               "fontconfig", "__pycache__"]

lol = [ [x for x in a.binaries if x[0].find(y) >= 0] for y in remove_strs]
remove_items = [item for sublist in lol for item in sublist]
a.binaries -= remove_items

#print("\n".join([str(x) for x in a.binaries]))
             
# for some reason, on a Mac, PyInstaller tries to include the entire
# source directory, including docs, examples, and build files!

# (also get rid of all the timezone files; pytz is included because it's
# a pandas dependency, but we don't do any timezone manipulation)

#remove_first = [ "cytoflow", "build", "dist", "doc", ".git", "pytz"]
#lol = [ [x for x in a.datas if x[0].startswith(y)] for y in remove_first]
#remove_items = [item for sublist in lol for item in sublist]

#a.datas -= remove_items

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz,
          a.scripts,
          [],
          #[('u', None, 'OPTION'), ('v', None, 'OPTION')],
          exclude_binaries=True,
          name='cytoflow',
          debug=False,
          #debug=True,
          strip=False,
          upx=False,
          console=False,
          #console=True,
          bootloader_ignore_signals=False,
          icon='cytoflowgui/images/icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='cytoflow',
               icon='cytoflowgui/images/icon.ico')

if sys.platform == 'darwin':
   app = BUNDLE(coll,
                name = "Cytoflow.app",
                icon = "cytoflowgui/images/icon.icns",
                bundle_identifier=None)



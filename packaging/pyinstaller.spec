import sys

sys.setrecursionlimit(10000) # or more

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
                       'PySide.QtNetwork', 'PySide.QtSvg',
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
             
# for some reason, on a Mac, PyInstaller tries to include the entire
# source directory, including docs, examples, and build files!

remove_first = [ "cytoflow", "build", "dist", "doc", ".git"]
lol = [ [x for x in a.datas if x[0].startswith(y)] for y in remove_first]
remove_items = [item for sublist in lol for item in sublist]
a.datas -= remove_items

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='cytoflow',
          debug=False,
          strip=False,
          upx=True,
          console=False,
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




block_cipher = None

a = Analysis(['cytoflowgui/run.py'],
             pathex=['cytoflowgui/'],
             binaries=None,
             datas=[('cytoflowgui/preferences.ini', '.'),
                    ('cytoflowgui/images', 'images'),
                    ('cytoflowgui/op_plugins/images', 'op_plugins/images'),
                    ('cytoflowgui/view_plugins/images', 'view_plugins/images')],
             hiddenimports = [
             'matplotlib.backends.backend_qt4agg',
             'matplotlib_backend',
             'pyface.ui.qt4.about_dialog',
             'pyface.ui.qt4.action.action_item',
             'pyface.ui.qt4.action.menu_bar_manager',
             'pyface.ui.qt4.action.menu_manager',
             'pyface.ui.qt4.action.status_bar_manager',
             'pyface.ui.qt4.action.tool_bar_manager',
             'pyface.ui.qt4.action.tool_palette_manager',
             'pyface.ui.qt4.application_window',
             'pyface.ui.qt4.beep',
             'pyface.ui.qt4.clipboard',
             'pyface.ui.qt4.confirmation_dialog',
             'pyface.ui.qt4.dialog',
             'pyface.ui.qt4.directory_dialog',
             'pyface.ui.qt4.file_dialog',
             'pyface.ui.qt4.gui',
             'pyface.ui.qt4.heading_text',
             'pyface.ui.qt4.image_cache',
             'pyface.ui.qt4.image_resource',
             'pyface.ui.qt4.init', 
             'pyface.ui.qt4.ipython_widget',
             'pyface.ui.qt4.message_dialog',
             'pyface.ui.qt4.progress_dialog',
             'pyface.ui.qt4.python_editor',
             'pyface.ui.qt4.python_shell',
             'pyface.ui.qt4.resource_manager',
             'pyface.ui.qt4.splash_screen',
             'pyface.ui.qt4.split_widget',
             'pyface.ui.qt4.system_metrics',
             'pyface.ui.qt4.tasks.advanced_editor_area_pane',
             'pyface.ui.qt4.tasks.dock_pane',
             'pyface.ui.qt4.tasks.editor',
             'pyface.ui.qt4.tasks.editor_area_pane',
             'pyface.ui.qt4.tasks.split_editor_area_pane',
             'pyface.ui.qt4.tasks.task_pane',
             'pyface.ui.qt4.tasks.task_window_backend',
             'pyface.ui.qt4.timer.do_later',
             'pyface.ui.qt4.timer.timer',
             'pyface.ui.qt4.widget',
             'pyface.ui.qt4.window',
             'pyface.ui.qt4.wizard.wizard',
             'pyface.ui.qt4.wizard.wizard_page',
             'pyface.ui.qt4.workbench.editor',
             'pyface.ui.qt4.workbench.view',
             'sklearn.neighbors.ball_tree',
             'sklearn.neighbors.kd_tree',
             'sklearn.neighbors.dist_metrics',
             'sklearn.neighbors.typedefs'
             ],
             hookspath=['pyinstaller'],
             runtime_hooks=['pyinstaller/rthook_pyqt4.py'],
             excludes=['gi.repository.Gio', 'gi.repository.GModule',
                       'gi.repository.GObject', 'gi.repository.Gtk',
                       'gi.repository.Gdk', 'gi.repository.Atk',
                       'gi.repository.cairo', 'gi.repository.GLib',
                       'gobject', 'Tkinter', 'FixTk', 'PyQt5',
                       'PySide', 'PySide.QtCore', 'PySide.QtGui',
                       'PySide.QtNetwork', 'PySide.QtSvg',
                       'pyface.wx', 'traitsui.wx', 'OpenGL',
                       'OpenGL.GLUT', 'OpenGL.platform',
                       'IPython', 'PyQt4.QtAssistant',
                       'PyQt4.QtNetwork', 'PyQt4.QtWebKit',
                       'PyQt4.QtSql', 'PyQt4.QtXml', 'PyQt4.QtTest', 
                       'PyQt4.QtOpenGL', 'wx',
                       'gtk', 'gi', 'sphinx', 'twisted', 'zope',
                       'jinja2', 'httplib2', '_mysql',
                       'sqlalchemy'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

# remove a few more egregiously unnecessary libraries and datas

remove_strs = ["nvidia", "Qt3Support", "QtDeclarative", "QtNetwork",
               "QtOpenGL", "QtScript", "Xml", "xml", "Sql", "sql", 
               "glib", "gobject", "sample_data"]

lol = [ [x for x in a.binaries if x[0].find(y) >= 0] for y in remove_strs]
remove_items = [item for sublist in lol for item in sublist]
a.binaries -= remove_items

lol = [ [x for x in a.datas if x[0].find(y) >= 0] for y in remove_strs]
remove_items = [item for sublist in lol for item in sublist]
a.datas -= remove_items

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='run',
          debug=False,
          strip=False,
          upx=True,
          console=False )

# for a one-directory install

# exe = EXE(pyz,
#           a.scripts,
#           exclude_binaries=True,
#           name='run',
#           debug=True,
#           strip=False,
#           upx=True,
#           console=True )
# 
# coll = COLLECT(exe,
#                a.binaries,
#                a.zipfiles,
#                a.datas,
#                strip=False,
#                upx=True,
#                name='run')

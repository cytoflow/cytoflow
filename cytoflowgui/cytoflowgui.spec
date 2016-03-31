# -*- mode: python -*-

block_cipher = None


a = Analysis(['run.py'],
             pathex=['./'],
             binaries=None,
             datas=[],
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
             hookspath=[],
             runtime_hooks=['rthook_pyqt4.py'],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

##### include mydir in distribution #######
def extra_datas(mydir):
    def rec_glob(p, files):
        import os
        import glob
        for d in glob.glob(p):
            if os.path.isfile(d):
                files.append(d)
                rec_glob("%s/*" % d, files)
    files = []
    rec_glob("%s/*" % mydir, files)
    extra_datas = []
    for f in files:
        extra_datas.append((f, f, 'DATA'))

    return extra_datas
###########################################

# append the 'data' dir
a.datas.append(('preferences.ini', './preferences.ini', 'DATA'))
a.datas += extra_datas('./images')
a.datas += extra_datas('./op_plugins/images')
a.datas += extra_datas('./view_plugins/images')
a.datas += extra_datas('./pyface/images')

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

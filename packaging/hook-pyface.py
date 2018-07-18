from PyInstaller.utils.hooks import (copy_metadata, collect_submodules, 
                                     collect_data_files)
datas = copy_metadata('pyface') + collect_data_files('pyface')

hiddenimports = collect_submodules('pyface.ui.qt4') + \
                collect_submodules('pyface.ui.qt4.action')


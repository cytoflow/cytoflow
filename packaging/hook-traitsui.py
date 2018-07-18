from PyInstaller.utils.hooks import copy_metadata, collect_submodules
datas = copy_metadata('traitsui')

hiddenimports = collect_submodules('traitsui.qt4')

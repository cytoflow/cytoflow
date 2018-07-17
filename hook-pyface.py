from PyInstaller.utils.hooks import copy_metadata
datas = copy_metadata('pyface') + copy_metadata('traitsui')


from PyInstaller.utils.hooks import copy_metadata
datas = copy_metadata('traitsui') + copy_metadata('pyface')


# from PyInstaller.compat import is_darwin
from PyInstaller.utils.hooks import (logger, collect_data_files, 
                                     collect_submodules)
import os

# get some missing datas and dynamically loaded submodules
datas = collect_data_files('pyface', 'images')
hiddenimports = collect_submodules("pyface")
# 
# hiddenimports = collect_submodules("pyface", subdir = os.path.join("ui", "qt4"))
# hiddenimports.extend(collect_submodules("pyface", subdir = os.path.join("ui", "qt4", "action")))
# hiddenimports.extend(collect_submodules("pyface", subdir = os.path.join("ui", "qt4", "tasks")))



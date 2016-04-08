# from PyInstaller.compat import is_darwin
from PyInstaller.utils.hooks import (logger, collect_data_files, 
                                     collect_submodules)
import os

datas = collect_data_files('pyface', 'images')
hiddenimports = collect_submodules("pyface", subdir = os.path.join("ui", "qt4"))
hiddenimports.extend(collect_submodules("pyface", subdir = os.path.join("ui", "qt4", "action")))
hiddenimports.extend(collect_submodules("pyface", subdir = os.path.join("ui", "qt4", "tasks")))

# 
# 
# import os
# import inspect
# import pyface
# import pkgutil
# 
# pyface_init = inspect.getfile(pyface)
# pyface_dir = os.path.dirname(pyface_init)
# pyface_images_dir = os.path.join(pyface_dir, "images")
# logger.info("Importing PyFace images")
# datas = [(pyface_images_dir, "pyface/images")]
# 
# qt_dir = os.path.join(pyface_dir, "ui", "qt4")
# 
# logger.info("Importing QT Pyface backend")
# 
# hiddenimports = []
# 
# # this imports most of the Qt backend; not the code editor, console, timer
# # util, wizard or workbench
# 
# logger.info(qt_dir)
# for _, name, _ in pkgutil.iter_modules([qt_dir], "pyface.ui.qt4."):
#     logger.info(name)
#     hiddenimports.append(name)
#     
# qt_action_dir = os.path.join(qt_dir, "action")
# for _, name, _ in pkgutil.iter_modules([qt_action_dir], "pyface.ui.qt4.action."):
#     logger.info(name)
#     hiddenimports.append(name)
#     
# qt_tasks_dir = os.path.join(qt_dir, "tasks")
# for _, name, _ in pkgutil.iter_modules([qt_tasks_dir], "pyface.ui.qt4.tasks."):
#     logger.info(name)
#     hiddenimports.append(name)


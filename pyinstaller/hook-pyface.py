from PyInstaller.compat import is_darwin
from PyInstaller.utils.hooks import (
    eval_statement, exec_statement, logger)

import os
import inspect
import pyface

pyface_init = inspect.getfile(pyface)
pyface_dir = os.path.dirname(pyface_init)
pyface_images_dir = os.path.join(pyface_dir, "images")
logger.info("Importing PyFace images")
datas = [(pyface_images_dir, "pyface/images")]

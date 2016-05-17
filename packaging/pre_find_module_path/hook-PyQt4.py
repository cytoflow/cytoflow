import os
import sys

import PyInstaller.utils.hooks
from PyInstaller.compat import is_darwin

def qt_menu_nib_dir(namespace):
  return ''

def pre_find_module_path(hook_api):
    if is_darwin:
        PyInstaller.utils.hooks.qt_menu_nib_dir = qt_menu_nib_dir

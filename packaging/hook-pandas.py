from PyInstaller.utils.hooks import collect_submodules
"""
Fixes issue #2978 with pandas version 0.21
(Pandas missing `pandas._libs.tslibs.timedeltas.so`)
"""

hiddenimports = ['pandas._libs.tslibs.timedeltas', 'pandas._libs.tslibs.np_datetime', 'pandas._libs.tslibs.nattype', 'pandas._libs.skiplist']

#hiddenimports = collect_submodules('pandas._libs')


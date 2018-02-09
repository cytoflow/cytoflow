"""
Fixes issue #2978 with pandas version 0.21
(Pandas missing `pandas._libs.tslibs.timedeltas.so`)
"""

hiddenimports = ['pandas._libs.tslibs.timedeltas']

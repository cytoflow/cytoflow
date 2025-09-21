from PyInstaller.utils.hooks import (copy_metadata, collect_submodules, 
                                     collect_data_files)

datas = collect_data_files('sklearn')

hiddenimports = collect_submodules('sklearn.externals')
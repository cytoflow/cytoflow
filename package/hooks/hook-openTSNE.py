from PyInstaller.utils.hooks import (copy_metadata, collect_submodules, 
                                     collect_data_files)

datas = copy_metadata('openTSNE') + collect_data_files('openTSNE')

hiddenimports = collect_submodules('openTSNE._tsne') + \
                collect_submodules('openTSNE._matrix_mul')
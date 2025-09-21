from PyInstaller.utils.hooks import (copy_metadata, collect_submodules, 
                                     collect_data_files)

datas = copy_metadata('scipy') + collect_data_files('scipy')

hiddenimports = collect_submodules('scipy._cyutility') + \
                collect_submodules('scipy._lib') 
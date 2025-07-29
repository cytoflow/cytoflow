from PyInstaller.utils.hooks import collect_submodules, copy_metadata, collect_data_files

datas = copy_metadata('matplotlib') + collect_data_files('matplotlib')

hiddenimports = collect_submodules('matplotlib.backends.backend_ps') + \
                collect_submodules('matplotlib.backends.backend_pdf') + \
                collect_submodules('matplotlib.backends.backend_svg') + \
                collect_submodules('matplotlib.backends.backend_pgf')
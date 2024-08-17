from PyInstaller.utils.hooks import collect_data_files

# Override the hook -- we don't need all these files and they REALLY 
# slow down the installer on Windows
# datas = collect_data_files('pytz')


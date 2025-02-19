from PyInstaller.utils.hooks import copy_metadata

datas = copy_metadata('cytoflow') + \
        copy_metadata('numpy') + \
        copy_metadata('pandas') + \
        copy_metadata('matplotlib') + \
        copy_metadata('bottleneck') + \
        copy_metadata('numexpr') + \
        copy_metadata('scipy') + \
        copy_metadata('scikit-learn') + \
        copy_metadata('seaborn') + \
        copy_metadata('statsmodels') + \
        copy_metadata('natsort') + \
        copy_metadata('numba') + \
        copy_metadata('traits') + \
        copy_metadata('traitsui') + \
        copy_metadata('pyface') + \
        copy_metadata('envisage') + \
        copy_metadata('nbformat') + \
        copy_metadata('yapf') 
        
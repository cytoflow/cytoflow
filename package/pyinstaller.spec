import sys, os, re, weakref, glob, logging

#
# patch PyInstaller.utils.hooks.qt.add_qt5_dependencies to work with
# conda
# 

from PyInstaller.utils.hooks import get_module_file_attribute
from PyInstaller.depend.bindepend import getImports, getfullnameof
from PyInstaller.compat import is_win, is_darwin, is_linux
from PyInstaller.utils.hooks.qt import qt_plugins_binaries, _qt_dynamic_dependencies_dict, pyqt5_library_info

def add_qt5_dependencies(hook_file):
    logger = logging.getLogger('PyInstaller.utils.hooks')
    # Accumulate all dependencies in a set to avoid duplicates.
    hiddenimports = set()
    translations_base = set()
    plugins = set()

    # Find the module underlying this Qt hook: change
    # ``/path/to/hook-PyQt5.blah.py`` to ``PyQt5.blah``.
    hook_name, hook_ext = os.path.splitext(os.path.basename(hook_file))
    assert hook_ext.startswith('.py')
    assert hook_name.startswith('hook-')
    module_name = hook_name[5:]
    namespace = module_name.split('.')[0]
    if namespace not in ('PyQt5', 'PySide2'):
        raise Exception('Invalid namespace: {0}'.format(namespace))
    is_PyQt5 = namespace == 'PyQt5'

    # Exit if the requested library can't be imported.
    if ((is_PyQt5 and not pyqt5_library_info.version) or
        (not is_PyQt5 and not pyside2_library_info.version)):
        return [], [], []

    # Look up the module returned by this import.
    module = get_module_file_attribute(module_name)
    logger.debug('add_qt5_dependencies: Examining %s, based on hook of %s.',
                 module, hook_file)

    # Walk through all the static dependencies of a dynamically-linked library
    # (``.so``/``.dll``/``.dylib``).
    imports = set(getImports(module))
    while imports:
        imp = imports.pop()

        # On Windows, find this library; other platforms already provide the
        # full path.
        if is_win:
            imp = getfullnameof(imp,
                # First, look for Qt binaries in the local Qt install.
                pyqt5_library_info.location['BinariesPath'] if is_PyQt5 else
                pyside2_library_info.location['BinariesPath']
            )

        # Strip off the extension and ``lib`` prefix (Linux/Mac) to give the raw
        # name. Lowercase (since Windows always normalized names to lowercase).
        lib_name = os.path.splitext(os.path.basename(imp))[0].lower()
        # Linux libraries sometimes have a dotted version number --
        # ``libfoo.so.3``. It's now ''libfoo.so``, but the ``.so`` must also be
        # removed.
        if is_linux and os.path.splitext(lib_name)[1] == '.so':
            lib_name = os.path.splitext(lib_name)[0]
        if lib_name.startswith('lib'):
            lib_name = lib_name[3:]
        # Mac: rename from ``qt`` to ``qt5`` to match names in Windows/Linux.
### BEGIN PATCH
        if is_darwin and lib_name.startswith('qt') and not lib_name.startswith('qt5'):
            lib_name = 'qt5' + lib_name[2:]
        elif is_darwin and lib_name.startswith('qt5'):
            lib_name = 'qt5' + lib_name[3:]

        if is_darwin and len(os.path.splitext(lib_name)) > 1:
            lib_name = os.path.splitext(lib_name)[0]
### END PATCH

        # match libs with QT_LIBINFIX set to '_conda', i.e. conda-forge builds
        if lib_name.endswith('_conda'):
            lib_name = lib_name[:-6]

        logger.debug('add_qt5_dependencies: raw lib %s -> parsed lib %s',
                     imp, lib_name)

        # Follow only Qt dependencies.
        if lib_name in _qt_dynamic_dependencies_dict:
            # Follow these to find additional dependencies.
            logger.debug('add_qt5_dependencies: Import of %s.', imp)
            imports.update(getImports(imp))
            # Look up which plugins and translations are needed.
            dd = _qt_dynamic_dependencies_dict[lib_name]
            lib_name_hiddenimports, lib_name_translations_base = dd[:2]
            lib_name_plugins = dd[2:]
            # Add them in.
            if lib_name_hiddenimports:
                hiddenimports.update([namespace + lib_name_hiddenimports])
            plugins.update(lib_name_plugins)
            if lib_name_translations_base:
                translations_base.update([lib_name_translations_base])

    # Change plugins into binaries.
    binaries = []
    for plugin in plugins:
        more_binaries = qt_plugins_binaries(plugin, namespace=namespace)
        binaries.extend(more_binaries)
    # Change translation_base to datas.
    tp = (
        pyqt5_library_info.location['TranslationsPath'] if is_PyQt5
        else pyside2_library_info.location['TranslationsPath']
    )
    datas = []
    for tb in translations_base:
        src = os.path.join(tp, tb + '_*.qm')
        # Not all PyQt5 installations include translations. See
        # https://github.com/pyinstaller/pyinstaller/pull/3229#issuecomment-359479893
        # and
        # https://github.com/pyinstaller/pyinstaller/issues/2857#issuecomment-368744341.
        if glob.glob(src):
            datas.append((
                src, os.path.join(
                    # The PySide2 Windows wheels place translations in a
                    # different location.
                    namespace, '' if not is_PyQt5 and is_win else 'Qt',
                    'translations'
                )
            ))
        else:
            logger.warning('Unable to find Qt5 translations %s. These '
                           'translations were not packaged.', src)
    # Change hiddenimports to a list.
    hiddenimports = list(hiddenimports)

    logger.debug('add_qt5_dependencies: imports from %s:\n'
                 '  hiddenimports = %s\n'
                 '  binaries = %s\n'
                 '  datas = %s',
                 hook_name, hiddenimports, binaries, datas)
    return hiddenimports, binaries, datas

import PyInstaller.utils.hooks.qt
PyInstaller.utils.hooks.qt.add_qt5_dependencies = add_qt5_dependencies


# make sure user-provided rthooks are processed after shipped rthooks

from PyInstaller.compat import VALID_MODULE_TYPES
def analyze_runtime_hooks(self, custom_runhooks):
    logger = logging.getLogger('PyInstaller.depend.analysis')

    rthooks_nodes = []
    logger.info('Analyzing run-time hooks ...')

    temp_toc = self._make_toc(VALID_MODULE_TYPES)
    for (mod_name, path, typecode) in temp_toc:
        # Look if there is any run-time hook for given module.
        if mod_name in self._available_rthooks:
            # There could be several run-time hooks for a module.
            for hook in self._available_rthooks[mod_name]:
                logger.info("Including run-time hook %r", hook)
                path = os.path.join(self._homepath, 'PyInstaller', 'loader', 'rthooks', hook)
                rthooks_nodes.append(self.run_script(path))

    if custom_runhooks:
        for hook_file in custom_runhooks:
            logger.info("Including custom run-time hook %r", hook_file)
            hook_file = os.path.abspath(hook_file)
            # Not using "try" here because the path is supposed to
            # exist, if it does not, the raised error will explain.
            rthooks_nodes.append(self.run_script(hook_file))

    return rthooks_nodes

from PyInstaller.depend.analysis import PyiModuleGraph
PyiModuleGraph.analyze_runtime_hooks = analyze_runtime_hooks

a = Analysis(['../cytoflowgui/run.py'],
             pathex=['cytoflowgui/'],
             binaries=None,
             datas=[('../cytoflowgui/preferences.ini', 'cytoflowgui'),
                    ('../cytoflowgui/images', '.'),
                    ('../cytoflowgui/op_plugins/images', 'cytoflowgui/op_plugins/images'),
                    ('../cytoflowgui/view_plugins/images', 'cytoflowgui/view_plugins/images'),
                    ('../cytoflowgui/help', 'cytoflowgui/help')],
             hiddenimports = ['matplotlib.backends.backend_qt5agg'],
             hookspath=['package/hooks'],
             runtime_hooks=['package/hooks/rthook_qtapi.py',
                            'package/hooks/rthook_qt5webengine.py',
                            'package/hooks/rthook_qtconf.py'],
             excludes=['gi.repository.Gio', 'gi.repository.GModule',
                       'gi.repository.GObject', 'gi.repository.Gtk',
                       'gi.repository.Gdk', 'gi.repository.Atk',
                       'gi.repository.cairo', 'gi.repository.GLib',
                       'gobject', 'Tkinter', 'FixTk', '_tkinter',
                       'PySide', 'PySide.QtCore', 'PySide.QtGui',
                       'PySide.QtNetwork', 'PySide.QtSvg', 'PyQt4',
                       'PyQt5.QtBluetooth', 'PyQt5.QtDesigner',
                       'PyQt5.QtHelp', 'PyQt5.QtLocation',
                       'PyQt5.QtMultimediaWidgets', 'PyQt5.QtNfc', 
                       'PyQt5.QtQml', 'PyQt5.QtQuick', 'PyQt5.QtQuickWidgets',
                       'PyQt5.QtSensors', 'PyQt5.QtSerialPort', 'PyQt5.QtSql',
                       'PyQt5.QtTest', 'PyQt5.QtWebSockets', 'PyQt5.QtXml',
                       'PyQt5.QtXmlPatterns',
                       'pyface.wx', 'traitsui.wx', 'IPython','wx',
                       'gtk', 'gi', 'sphinx', 'twisted', 'zope',
                       'jinja2', 'httplib2', '_mysql',
                       'sqlalchemy', 'zmq'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None)

# remove a few libraries that cause crashes if we don't use the system
# versions

remove_strs = ["glib", "gobject", "gthread", "libX", "libICE", "libdrm"]

# on linux, Anaconda version of fontconfig looks for fonts bundled with
# Anaconda instead of the system fonts.  this is fine if you're running
# Anaconda, but breaks the 

remove_strs.append('libfontconfig')
remove_strs.append('libuuid')

lol = [ [x for x in a.binaries if x[0].find(y) >= 0] for y in remove_strs]
remove_items = [item for sublist in lol for item in sublist]
a.binaries -= remove_items

# for some reason, on a Mac, PyInstaller tries to include the entire
# source directory, including docs, examples, and build files!

# (also get rid of all the timezone files; pytz is included because it's
# a pandas dependency, but we don't do any timezone manipulation)

#remove_first = [ "cytoflow", "build", "dist", "doc", ".git", "pytz"]

# get rid of the timezone files; pytz is a pandas dependency, but we
# don't do any timezone manipulation and it makes the Windows installer
# REALLY slow

# remove_first = ['pytz']
# lol = [ [x for x in a.datas if x[0].startswith(y)] for y in remove_first]
# remove_items = [item for sublist in lol for item in sublist]

# a.datas -= remove_items

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(pyz,
          a.scripts,
          [],
          #[('u', None, 'OPTION'), ('v', None, 'OPTION')],
          exclude_binaries=True,
          name='cytoflow',
          debug=False,
          #debug=True,
          strip=False,
          upx=False,
          console=False,
          #console=True,
          bootloader_ignore_signals=False,
          icon='icon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='cytoflow',
               icon='icon.ico')

if sys.platform == 'darwin':
   app = BUNDLE(coll,
                name = "Cytoflow.app",
                icon = "icon.icns",
                bundle_identifier=None)



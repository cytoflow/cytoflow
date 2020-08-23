import sys, os, re, weakref, glob

# monkey-patch PyInstaller 3.6 to allow for user hooks to override
# provided ones.  this won't be required for PyInstaller 4.0, thankfully.
# (adapted from https://github.com/pyinstaller/pyinstaller/commit/d355a49e829aa4fed959df51d18a193a4d321c21)

from PyInstaller.compat import importlib_load_source, VALID_MODULE_TYPES
from PyInstaller import log as logging
from PyInstaller import configure

from PyInstaller.depend.analysis import PyiModuleGraph
from PyInstaller.depend.imphook import ModuleHookCache, AdditionalFilesCache, \
                                       _MAGIC_MODULE_HOOK_ATTRS, HOOKS_MODULE_NAMES

# patch 1 - change hooks directory search order

def _cache_hooks(self, hook_type):
    system_hook_dir = configure.get_importhooks_dir(hook_type)

    hook_dirs = [system_hook_dir]
    for user_hook_dir in self._user_hook_dirs:
        user_hook_type_dir = os.path.join(user_hook_dir, hook_type)
        if os.path.isdir(user_hook_type_dir):
            hook_dirs.insert(0, user_hook_type_dir)

    return ModuleHookCache(self, hook_dirs)

PyiModuleGraph._cache_hooks = _cache_hooks

# patch 2 - change how ModuleHooks are copied

from PyInstaller.depend.imphook import ModuleHook
def __init__(self, module_graph, module_name, hook_filename,
             hook_module_name_prefix):

        assert isinstance(module_graph, weakref.ProxyTypes)
        self.module_graph = module_graph
        self.module_name = module_name
        self.hook_filename = hook_filename

        self.hook_module_name = (
            hook_module_name_prefix + self.module_name.replace('.', '_'))

        # THIS IS THE CHANGED BIT
        global HOOKS_MODULE_NAMES
        if self.hook_module_name in HOOKS_MODULE_NAMES:
            # When self._shallow is true, this class never loads the hook and
            # sets the attributes to empty values
            self._shallow = True
        else:
            self._shallow = False
            HOOKS_MODULE_NAMES.add(self.hook_module_name)

        # Attributes subsequently defined by the _load_hook_module() method.
        self._hook_module = None

ModuleHook.__init__ = __init__

# patch 3 - check if a hook has been loaded; if so, don't load another

def _load_hook_module(self):

    logger = logging.getLogger(__name__)

    # If this hook script module has already been loaded,
    # or we are _shallow, noop.
    if self._hook_module is not None or self._shallow:

        if self._shallow:
            self._hook_module = True  # Not None

            # Inform the user

            logger.debug(
                'Skipping module hook %r from %r because a hook for %s has'
                ' already been loaded.',
                *os.path.split(self.hook_filename)[::-1], self.module_name
            )

            # Set the default attributes to empty instances of the type.
            for attr_name, (attr_type, _) in _MAGIC_MODULE_HOOK_ATTRS.items():
                super(ModuleHook, self).__setattr__(attr_name, attr_type())
        return

    # Load and execute the hook script. Even if mechanisms from the import
    # machinery are used, this does not import the hook as the module.
    head, tail = os.path.split(self.hook_filename)
    logger.info(
        'Loading module module hook %r from %r...', tail, head)
    self._hook_module = importlib_load_source(
        self.hook_module_name, self.hook_filename)

    # Copy hook script attributes into magic attributes exposed as instance
    # variables of the current "ModuleHook" instance.
    for attr_name, (default_type, sanitizer_func) in (
        _MAGIC_MODULE_HOOK_ATTRS.items()):
        # Unsanitized value of this attribute.
        attr_value = getattr(self._hook_module, attr_name, None)

        # If this attribute is undefined, expose a sane default instead.
        if attr_value is None:
            attr_value = default_type()
        # Else if this attribute requires sanitization, do so.
        elif sanitizer_func is not None:
            attr_value = sanitizer_func(attr_value)
        # Else, expose the unsanitized value of this attribute.

        # Expose this attribute as an instance variable of the same name.
        setattr(self, attr_name, attr_value)

ModuleHook._load_hook_module = _load_hook_module

# patch 4 - make AdditionalFilesCache not blow away datas and binaries

def add(self, modname, binaries, datas):
    self._binaries.setdefault(modname, list())
    self._binaries[modname].extend(binaries)

    self._datas.setdefault(modname, list())
    self._datas[modname].extend(datas)

AdditionalFilesCache.add = add

# patch 5 - instead of implementing the whole new rthook scheme,
#           just make sure user-provided rthooks are processed after
#           shipped rthooks

def analyze_runtime_hooks(self, custom_runhooks):
    logger = logging.getLogger(__name__)

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

PyiModuleGraph.analyze_runtime_hooks = analyze_runtime_hooks

#
# patch PyInstaller.utils.hooks.qt.add_qt5_dependencies to work with
# conda
# 

from PyInstaller.utils.hooks import get_module_file_attribute
from PyInstaller.depend.bindepend import getImports, getfullnameof
from PyInstaller.compat import is_py3, is_win, is_darwin, is_linux
from PyInstaller.utils.hooks.qt import qt_plugins_binaries, _qt_dynamic_dependencies_dict, pyqt5_library_info

# add_qt5_dependencies
# --------------------
# Find the Qt dependencies based on the hook name of a PyQt5 hook. Returns
# (hiddenimports, binaries, datas). Typical usage: ``hiddenimports, binaries,
# datas = add_qt5_dependencies(__file__)``.
def add_qt5_dependencies(hook_file):

    logger = logging.getLogger(__name__)
 
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
    if namespace != 'PyQt5':
        raise Exception('Invalid namespace: {0}'.format(namespace))

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
            imp = getfullnameof(imp)

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
        if is_darwin and lib_name.startswith('qt') and not lib_name.startswith('qt5'):
            lib_name = 'qt5' + lib_name[2:]
        elif is_darwin and lib_name.startswith('qt5'):
            lib_name = 'qt5' + lib_name[3:]
        if is_darwin and len(os.path.splitext(lib_name)) > 1:
            lib_name = os.path.splitext(lib_name)[0]

        logger.debug('add_qt5_dependencies: raw lib %s -> parsed lib %s',
                     imp, lib_name)

        # Follow only Qt dependencies.
        if lib_name in _qt_dynamic_dependencies_dict:
            # Follow these to find additional dependencies.
            logger.debug('add_qt5_dependencies: Import of %s.', imp)
            imports.update(getImports(imp))
            # Look up which plugins and translations are needed. Avoid Python
            # 3-only syntax, since the Python 2.7 parser will raise an
            # exception. The original statment was:
            ## (lib_name_hiddenimports, lib_name_translations_base,
            ## *lib_name_plugins) = _qt_dynamic_dependencies_dict[lib_name]
            dd = _qt_dynamic_dependencies_dict[lib_name]
            lib_name_hiddenimports, lib_name_translations_base = dd[:2]
            lib_name_plugins = dd[2:]
            # Add them in.
            if lib_name_hiddenimports:
                hiddenimports.update([lib_name_hiddenimports])
            plugins.update(lib_name_plugins)
            if lib_name_translations_base:
                translations_base.update([lib_name_translations_base])

    # Change plugins into binaries.
    binaries = []
    for plugin in plugins:
        more_binaries = qt_plugins_binaries(plugin, namespace=namespace)
        binaries.extend(more_binaries)
    # Change translation_base to datas.
    tp = pyqt5_library_info.location['TranslationsPath']
    datas = []
    for tb in translations_base:
        src = os.path.join(tp, tb + '_*.qm')
        # Not all PyQt5 installations include translations. See
        # https://github.com/pyinstaller/pyinstaller/pull/3229#issuecomment-359479893
        # and
        # https://github.com/pyinstaller/pyinstaller/issues/2857#issuecomment-368744341.
        if glob.glob(src):
            datas.append( (src, os.path.join(namespace, 'Qt', 'translations')) )
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

from PyInstaller.__main__ import run
if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(run())

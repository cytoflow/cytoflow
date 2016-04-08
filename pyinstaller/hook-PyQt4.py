import PyInstaller
from PyInstaller.utils.hooks import logger
from os import listdir

extra_paths = ["/anaconda/lib"]

def getImports_macholib(pth):
    """
    Find the binary dependencies of PTH.
    This implementation is for Mac OS X and uses library macholib.
    """
    from PyInstaller.lib.macholib.MachO import MachO
    from PyInstaller.lib.macholib.mach_o import LC_RPATH
    from PyInstaller.lib.macholib.dyld import dyld_find
    rslt = set()
    seen = set()  # Libraries read from binary headers.

    ## Walk through mach binary headers.

    m = MachO(pth)
    for header in m.headers:
        for idx, name, lib in header.walkRelocatables():
            # Sometimes some libraries are present multiple times.
            if lib not in seen:
                seen.add(lib)

    # Walk through mach binary headers and look for LC_RPATH.
    # macholib can't handle @rpath. LC_RPATH has to be read
    # from the MachO header.
    # TODO Do we need to remove LC_RPATH from MachO load commands?
    #      Will it cause any harm to leave them untouched?
    #      Removing LC_RPATH should be implemented when getting
    #      files from the bincache if it is necessary.
    run_paths = set()
    for header in m.headers:
        for command in header.commands:
            # A command is a tupple like:
            #   (<macholib.mach_o.load_command object at 0x>,
            #    <macholib.mach_o.rpath_command object at 0x>,
            #    '../lib\x00\x00')
            cmd_type = command[0].cmd
            if cmd_type == LC_RPATH:
                rpath = str(command[2])
                # Remove trailing '\x00' characters.
                # e.g. '../lib\x00\x00'
                rpath = rpath.rstrip('\x00')
                # Make rpath absolute. According to Apple doc LC_RPATH
                # is always relative to the binary location.
                rpath = os.path.normpath(os.path.join(os.path.dirname(pth), rpath))
                run_paths.update([rpath])
            else:
                # Frameworks that have this structure Name.framework/Versions/N/Name
                # need to to search at the same level as the framework dir.
                # This is specifically needed so that the QtWebEngine dependencies
                # can be found.
                if '.framework' in pth:
                    run_paths.update(['../../../'])

    ## Try to find files in file system.

    # In cases with @loader_path or @executable_path
    # try to look in the same directory as the checked binary is.
    # This seems to work in most cases.
    exec_path = os.path.abspath(os.path.dirname(pth))

    # Add additional paths to library search
    run_paths.update(extra_paths)

    for lib in seen:

        # Suppose that @rpath is not used for system libraries and
        # using macholib can be avoided.
        # macholib can't handle @rpath.
        if lib.startswith('@rpath'):
            lib = lib.replace('@rpath', '.')  # Make path relative.
            final_lib = None  # Absolute path to existing lib on disk.
            # Try multiple locations.
            for run_path in run_paths:
                # @rpath may contain relative value. Use exec_path as
                # base path.
                if not os.path.isabs(run_path):
                    run_path = os.path.join(exec_path, run_path)
                # Stop looking for lib when found in first location.
                if os.path.exists(os.path.join(run_path, lib)):
                    final_lib = os.path.abspath(os.path.join(run_path, lib))
                    rslt.add(final_lib)
                    break
            # Log error if no existing file found.
            if not final_lib:
                logger.error('Can not find path %s (needed by %s)', lib, pth)

        # Macholib has to be used to get absolute path to libraries.
        else:
            # macholib can't handle @loader_path. It has to be
            # handled the same way as @executable_path.
            # It is also replaced by 'exec_path'.
            if lib.startswith('@loader_path'):
                lib = lib.replace('@loader_path', '@executable_path')
            try:
                lib = dyld_find(lib, executable_path=exec_path)
                rslt.add(lib)
            except ValueError:
                logger.error('Can not find path %s (needed by %s)', lib, pth)

    return rslt


if PyInstaller.compat.is_darwin:
   logger.info("Monkey-patching bindep._getImports_macholib")
   PyInstaller.depend.bindepend._getImports_macholib = getImports_macholib


import sys
import os

if sys.platform.startswith('win'):
    import multiprocessing.popen_spawn_win32 as forking  # @UnusedImport
else:
    import multiprocessing.popen_spawn_posix as forking  # @Reimport

import multiprocessing.spawn as multiprocessing_spawn
import multiprocessing

_is_forking = multiprocessing_spawn.is_forking
_set_start_method = multiprocessing.set_start_method

def __set_start_method(name, *args, **kwargs):
    if name == 'spawn':
        # First define a modified version of Popen.
        class _Popen(forking.Popen):
            def __init__(self, *args, **kw):
                if hasattr(sys, 'frozen'):
                    # We have to set original _MEIPASS2 value from sys._MEIPASS
                    # to get --onefile mode working.
                    os.putenv('_MEIPASS2', sys._MEIPASS)  # @UndefinedVariable
                try:
                    super(_Popen, self).__init__(*args, **kw)
                finally:
                    if hasattr(sys, 'frozen'):
                        # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                        # available. In those cases we cannot delete the variable
                        # but only set it to the empty string. The bootloader
                        # can handle this case.
                        if hasattr(os, 'unsetenv'):
                            os.unsetenv('_MEIPASS2')
                        else:
                            os.putenv('_MEIPASS2', '')

        def __is_forking(argv):
            expected = ['-B', '-s', '-S', '-E', '-c']
            for arg in expected:
                if arg not in argv:
                    return _is_forking(argv)
            sys.exit()

        multiprocessing_spawn.is_forking = __is_forking
        multiprocessing_spawn._fixup_main_from_path = lambda _: None
        forking.Popen = _Popen

        # Then, call  the correct 'freeze_support'
        multiprocessing_spawn.freeze_support()

    # finally, call the original method
    _set_start_method(name, *args, **kwargs)

multiprocessing.set_start_method = __set_start_method
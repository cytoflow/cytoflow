from PyInstaller import log as logging 
from PyInstaller import compat
from os import listdir

libdirs = [compat.base_prefix + "/lib", compat.base_prefix + "/Library/bin"]
for libdir in libdirs:
   try:
      mkllib = [x for x in listdir(libdir) if x.startswith('mkl_')
                                           or x.startswith('libmkl_')]
      if mkllib <> []: 
         logger = logging.getLogger(__name__)
         logger.info("Adding the MKL libraries to binaries.")
         binaries = [(libdir + "/" + l, '') for l in mkllib]
   except OSError:
      pass

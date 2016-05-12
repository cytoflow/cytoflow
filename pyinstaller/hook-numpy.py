from PyInstaller import log as logging 
from PyInstaller import compat
from os import listdir

libdirs = [compat.base_prefix + "/lib", compat.base_prefix + "/Library/bin"]
for libdir in libdirs:
   try:
      mkllib = [x for x in listdir(libdir) if x.startswith('mkl_')]
      if mkllib <> []: 
         logger = logging.getLogger(__name__)
         logger.info("MKL installed as part of numpy, importing that!")
         binaries = [(libdir + "/" + l, '') for l in mkllib]
   except FileNotFoundError:
      pass

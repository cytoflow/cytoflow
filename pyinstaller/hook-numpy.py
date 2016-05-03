from PyInstaller import log as logging 
from PyInstaller import compat
from os import listdir

libdir = compat.base_prefix + "/lib"
mkllib = filter(lambda x : x.startswith('libmkl_'), listdir(libdir))
if mkllib <> []: 
   logger = logging.getLogger(__name__)
   logger.info("MKL installed as part of numpy, importing that!")
   binaries = map(lambda l: (libdir + "/" + l, ''), mkllib)

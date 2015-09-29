'''
Created on Mar 7, 2015

@author: brian
'''

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import cytoflow

from run import run_gui

# for the easy-install entry script
easy_install_entry = lambda: run_gui([])

__version__ = cytoflow.__version__
'''
Created on Aug 5, 2020

@author: brian
'''
import logging, multiprocessing, sys, traceback
from pathlib import Path

from nose2.events import Plugin
from nose2.plugins.mp import MultiProcess, procserver

log = logging.getLogger(__name__)

# select the 'null' pyface toolkit. an exception is raised if the qt toolkit
# is subsequently imported, but that's better than trying to actually create
# a Qt app if PyQt is accidentally imported.

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'null'

# use the sphinx autodoc module-mocker to mock out traitsui.qt
# because when it's imported, it starts a Qt Application

from cytoflowgui.tests.sphinx_mock import MockFinder
sys.meta_path.insert(0, MockFinder(['traitsui.qt']))  

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import warnings

def _startProcs(self, test_count):
    # Create session export
    session_export = self._exportSession()
    procs = []
    count = min(test_count, self.procs)
    log.debug("Creating %i worker processes", count)
    for _ in range(0, count):
        parent_conn, child_conn = self._prepConns()
        proc = multiprocessing.Process(
            target=procserver, args=(session_export, child_conn))
        proc.start()
        parent_conn = self._acceptConns(parent_conn)
        procs.append((proc, parent_conn))
    return procs

def _get_running_interactive_framework():
    return "headless"

class NoseSetup(Plugin):
    configSection = 'nose_setup'
    saveFiguresFilename = None
    saveFiguresDevice = None
    
    def __init__(self):
        self.addFlag(self.setGui, 'GUI', 'runInGUI', 'Running in GUI?')
        self.addArgument(self.saveFigures, None, "saveFigures", 'Save matplotlib figures to this file. If not passed, discard them.')
        
    def createTests(self, event):
        # select the 'null' pyface toolkit. an exception is raised if the qt toolkit
        # is subsequently imported, but that's better than trying to actually create
        # a Qt app if PyQt is accidentally imported.
        
        from traits.etsconfig.api import ETSConfig
        ETSConfig.toolkit = 'null'
        
        # use the sphinx autodoc module-mocker to mock out traitsui.qt
        # because when it's imported, it starts a Qt Application
        
        from cytoflowgui.tests.sphinx_mock import MockFinder
        import sys; sys.meta_path.insert(0, MockFinder(['traitsui.qt']))   

    def startTestRun(self, _):
        log.debug('Loading customized nose2 configuration')

        # set multiprocessing to use spawn (defaults to fork on UNIX)
        # keeps (GNU) OpenMP from crashing 
        multiprocessing.set_start_method('spawn', force = True)
        
        # squash the matplotlib max figures warning
        matplotlib.rcParams.update({'figure.max_open_warning': 0})
        
        # run the mp plugin without making subprocesses daemons
        MultiProcess._startProcs = _startProcs
        
        # make matplotlib stop complaining about running headless
        matplotlib.backends._get_running_interactive_framework = _get_running_interactive_framework
        
        # set up pdf plot saving
        if self.saveFiguresFilename:
            self.saveFiguresDevice = PdfPages(self.saveFiguresFilename)
            
    def stopTestRun(self, _):
        if self.saveFiguresDevice:
            self.saveFiguresDevice.close()
            
    def registerInSubprocess(self, event):
        event.pluginClasses.append(self.__class__)
        
    def startSubprocess(self, _):
        # select the 'null' pyface toolkit.     
        from traits.etsconfig.api import ETSConfig
        ETSConfig.toolkit = 'null'
    
        # use the sphinx autodoc module-mocker to mock out traitsui.qt
    
        from cytoflowgui.tests.sphinx_mock import MockFinder
        import sys; sys.meta_path.insert(0, MockFinder(['traitsui.qt']))  
        
        # squash the matplotlib max figures warning
        matplotlib.rcParams.update({'figure.max_open_warning': 0})
        
    def stopTest(self, event):
        if self.saveFiguresDevice:
            for n in plt.get_fignums():
                plt.figure(n).savefig(self.saveFiguresDevice, format = 'pdf')
        plt.close('all')

    def setGui(self):
        # tell cytoflow that we are in a GUI, to test GUI-specific things!

        import cytoflow
        cytoflow.RUNNING_IN_GUI = True 

    def saveFigures(self, filename):
        filename = filename[0]
        if Path(filename).exists():
            raise RuntimeError("File {} already exists".format(filename))
        self.saveFiguresFilename = filename

        
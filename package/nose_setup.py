'''
Created on Aug 5, 2020

@author: brian
'''
import os, logging, multiprocessing

from nose2.events import Plugin
from nose2.plugins.mp import MultiProcess, procserver

import matplotlib
import matplotlib.backends

log = logging.getLogger('package.nose_setup')

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

    def startTestRun(self, event):
        log.warning('Loading customized nose2 configuration')
        
        # set multiprocessing to use spawn (defaults to fork on UNIX)
        # keeps (GNU) OpenMP from crashing 
        multiprocessing.set_start_method('spawn', force = True)
        
        # tell cytoflow that we are in a GUI, to test GUI-specific things!
        import cytoflow
        cytoflow.RUNNING_IN_GUI = True
        
        # squash the matplotlib max figures warning
        matplotlib.rcParams.update({'figure.max_open_warning': 0})
        
        # run the mp plugin without making subprocesses daemons
        MultiProcess._startProcs = _startProcs
        
        # set the OpenMP thread pool to 1
        # os.environ['OMP_NUM_THREADS'] = '1'
        
        # make matplotlib stop complaining about running headless
        matplotlib.backends._get_running_interactive_framework = _get_running_interactive_framework
        
        # set up some reasonable logging
        # Clear the default logging so we can use our own format
        rootLogger = logging.getLogger()
        list(map(rootLogger.removeHandler, rootLogger.handlers[:]))
        list(map(rootLogger.removeFilter, rootLogger.filters[:]))
        
        logging.getLogger().setLevel(logging.DEBUG)
        
        ## send the log to STDERR, but only WARN or higher
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
        console_handler.setLevel(logging.WARN)
        logging.getLogger().addHandler(console_handler)

        
        

        
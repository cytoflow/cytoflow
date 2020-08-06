'''
Created on Aug 5, 2020

@author: brian
'''
import os, logging, multiprocessing

from nose2.events import Plugin
from nose2.plugins.mp import MultiProcess, procserver

log = logging.getLogger('package.nose_setup')

def _startProcs(self, test_count):
    # Create session export
    session_export = self._exportSession()
    procs = []
    count = min(test_count, self.procs)
    log.debug("Creating %i worker processes", count)
    for i in range(0, count):
        parent_conn, child_conn = self._prepConns()
        proc = multiprocessing.Process(
            target=procserver, args=(session_export, child_conn))
        proc.start()
        parent_conn = self._acceptConns(parent_conn)
        procs.append((proc, parent_conn))
    return procs

class NoseSetup(Plugin):
    configSection = 'nose_setup'

    def startTestRun(self, event):
        log.warning('Loading customized nose2 configuration')
        
        MultiProcess._startProcs = _startProcs
        os.environ['OMP_NUM_THREADS'] = '1'

        
'''
Created on Apr 2, 2016

@author: brian
'''

from traits.api import HasStrictTraits, Any, List

from cytoflowgui.workflow_item import WorkflowItem

def start_worker_process(conn):
    p = WorkerProcess(conn = conn)
    p.wait_for_updates()

class WorkerProcess(HasStrictTraits):
    '''
    classdocs
    '''

    conn = Any
    workflow = List(WorkflowItem)
    
    def wait_for_updates(self):
        while True:
            msg = self.conn.recv()

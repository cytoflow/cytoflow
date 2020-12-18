#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Jan 4, 2018

@author: brian
'''

import unittest, multiprocessing, os

# do this at import time so we get lots of output when running 
# in PyDev, etc.
# logging.getLogger().setLevel(logging.DEBUG)

from traits.util.async_trait_wait import wait_for_condition

from cytoflowgui.workflow import Workflow, RemoteWorkflow
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.op_plugins import ImportPlugin

def remote_main(parent_workflow_conn, parent_mpl_conn, log_q, running_event):
    import matplotlib
    matplotlib.use('agg')

    running_event.set()
    RemoteWorkflow().run(parent_workflow_conn, parent_mpl_conn, log_q, headless = True)

class WorkflowTest(unittest.TestCase):
    
    def setUp(self):
        
        # communications channels
        parent_workflow_conn, child_workflow_conn = multiprocessing.Pipe()  
        parent_mpl_conn, child_matplotlib_conn = multiprocessing.Pipe()
        log_q = multiprocessing.Queue()
        running_event = multiprocessing.Event()
                
        remote_process = multiprocessing.Process(target = remote_main,
                                                 name = "remote process",
                                                 args = [parent_workflow_conn,
                                                         parent_mpl_conn,
                                                         log_q,
                                                         running_event])
        
        remote_process.daemon = True
        remote_process.start() 
        running_event.wait()
        
        self.workflow = Workflow((child_workflow_conn, child_matplotlib_conn, log_q))
        self.remote_process = remote_process

    def tearDown(self):
        self.workflow.shutdown_remote_process(self.remote_process)
        
class ImportedDataTest(WorkflowTest):
    
    def setUp(self):
        WorkflowTest.setUp(self)
        
        plugin = ImportPlugin()
        op = plugin.get_operation()

        from cytoflow import Tube
        
        op.conditions = {"Dox" : "float", "Well" : "category"}
     
        self.cwd = os.path.dirname(os.path.abspath(__file__))
     
        tube1 = Tube(file = self.cwd + "/../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs",
                     conditions = {"Dox" : 0.0, "Well" : 'A'})
     
        tube2 = Tube(file = self.cwd + "/../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs",
                     conditions = {"Dox" : 10.0, "Well" : 'A'})

        tube3 = Tube(file = self.cwd + "/../../cytoflow/tests/data/Plate01/YFP_Well_A7.fcs",
                     conditions = {"Dox" : 100.0, "Well" : 'A'})
         
        tube4 = Tube(file = self.cwd + "/../../cytoflow/tests/data/Plate01/CFP_Well_B4.fcs",
                     conditions = {"Dox" : 0.0, "Well" : 'B'})
     
        tube5 = Tube(file = self.cwd + "/../../cytoflow/tests/data/Plate01/RFP_Well_A6.fcs",
                     conditions = {"Dox" : 10.0, "Well" : 'B'})

        tube6 = Tube(file = self.cwd + "/../../cytoflow/tests/data/Plate01/YFP_Well_C7.fcs",
                     conditions = {"Dox" : 100.0, "Well" : 'B'})
     
        op.tubes = [tube1, tube2, tube3, tube4, tube5, tube6]
        
        wi = WorkflowItem(operation = op,
                          view_error = "Not yet plotted") 
        self.workflow.workflow.append(wi)
        op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'valid', wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[0].result is not None"))



class TasbeTest(WorkflowTest):
    
    def setUp(self):
        WorkflowTest.setUp(self)
        
        plugin = ImportPlugin()
        op = plugin.get_operation()

        from cytoflow import Tube
             
        self.cwd = os.path.dirname(os.path.abspath(__file__))
     
        tube = Tube(file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs")
        op.tubes = [tube]
        
        wi = WorkflowItem(operation = op,
                          view_error = "Not yet plotted") 
        self.workflow.workflow.append(wi)
        op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'valid', wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[0].result is not None"))


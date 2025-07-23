#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile
import pandas as pd

import cytoflow.utility as util

# needed for testing lambdas
from cytoflow import geom_mean, geom_sd  # @UnusedImport

from cytoflowgui.tests.test_base import WorkflowTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations import RegistrationWorkflowOp, RegistrationDiagnosticWorkflowView, ImportWorkflowOp, RegistrationChannel
from cytoflowgui.workflow.subset import CategorySubset, RangeSubset
from cytoflowgui.workflow.serialization import load_yaml, save_yaml

class TestRegister(WorkflowTest):
    
    def setUp(self):
        super().setUp()
        
        self.addTypeEqualityFunc(ImportWorkflowOp, 'assertHasTraitsEqual')  
        import_op = ImportWorkflowOp()

        from cytoflow import Tube
        
        import_op.conditions = {"Sample" : "category"}
     
        self.cwd = os.path.dirname(os.path.abspath(__file__))
     
        tube1 = Tube(file = self.cwd + "/../../cytoflow/tests/data/module_examples/itn_02.fcs",
                     conditions = {"Sample" : "2"})
     
        tube2 = Tube(file = self.cwd + "/../../cytoflow/tests/data/module_examples/itn_03.fcs",
                     conditions = {"Sample" : "3"})
                     
        import_op.tubes = [tube1, tube2]
        
        wi = WorkflowItem(operation = import_op,
                          status = "waiting",
                          view_error = "Not yet plotted") 
        self.workflow.workflow.append(wi)
        
        import_op.do_estimate = True
        self.workflow.wi_waitfor(wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[0].result is not None"))

        
        self.addTypeEqualityFunc(RegistrationWorkflowOp, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(RegistrationDiagnosticWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(RegistrationChannel, 'assertHasTraitsEqual')      

        self.op = op = RegistrationWorkflowOp()
        
        op.channels_list = [RegistrationChannel(channel = "CD3", scale = "log"),
                            RegistrationChannel(channel = "CD4", scale = "log")]
        op.by = ["Sample"]
        
        op.subset_list.append(CategorySubset(name = "Sample", values = ["2", "3"]))
        
        self.wi = wi = WorkflowItem(operation = op,
                                    status = 'waiting',
                                    view_error = "Not yet plotted")
        wi.views.append(self.wi.default_view)        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        # run estimate
        op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')

    def testEstimate(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   
    def testRemoveChannels(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channels_list.pop()
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
    
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testAddChannels(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channels_list.append(RegistrationChannel(channel = "CD8", scale = "log"))
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
    
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
    
    
    def testChangeScale(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channels_list[0].scale = "logicle"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
    
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))


    def testChangeKernel(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.kernel = "tophat"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
    
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        

    def testChangeBw(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.bw = "silverman"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
    
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
    

    def testChangeGrid(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.gridsize = 100
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
    
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
    

    def testChangeSubset(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.subset_list[0].selected = ["2", "3"]
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
    
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
    
    
    def testPlot(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.current_view = self.wi.default_view
        self.wi.current_view.current_plot = "CD3"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

    def testSerialize(self):
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
    
            save_yaml(self.op, filename)
            new_op = load_yaml(filename)
    
        finally:
            os.unlink(filename)
    
        self.maxDiff = None
        self.assertEqual(self.op, new_op)
    
    def testSerializeWorkflowItem(self):
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
    
            save_yaml(self.wi, filename)
            new_wi = load_yaml(filename)
    
        finally:
            os.unlink(filename)
    
        self.maxDiff = None
    
        self.assertEqual(self.wi, new_wi)
    
    def testNotebook(self):
        self.wi.current_view = self.wi.default_view
        self.wi.current_view.current_plot = "CD3"
        code = "import cytoflow as flow\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
    
            for view in wi.views:
                code = code + view.get_notebook_code(i)
    
        code_locals = {}
        with self.assertWarns(util.CytoflowWarning):
            exec(code, locals = code_locals)
    
        nb_data = code_locals['ex_1'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
    
        pd.testing.assert_frame_equal(nb_data, remote_data)


if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestGaussian1D.testEstimate']
    unittest.main()
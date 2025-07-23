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

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations import FlowPeaksWorkflowOp, FlowPeaksWorkflowView
from cytoflowgui.workflow.views import ScatterplotPlotParams, DensityPlotParams
from cytoflowgui.workflow.subset import CategorySubset, RangeSubset
from cytoflowgui.workflow.serialization import load_yaml, save_yaml

class TestFlowPeaks(ImportedDataTest):
    
    def setUp(self):
        super().setUp()
        
        self.addTypeEqualityFunc(FlowPeaksWorkflowOp, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(FlowPeaksWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(ScatterplotPlotParams, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(DensityPlotParams, 'assertHasTraitsEqual')

        self.op = op = FlowPeaksWorkflowOp()
        
        op.name = "FP"
        op.xchannel = "V2-A"
        op.ychannel = "Y2-A"
        op.xscale = "logicle"
        op.yscale = "logicle"
        op.h0 = 0.5
        
        op.subset_list.append(CategorySubset(name = "Well",
                                             values = ['A', 'B']))
        op.subset_list.append(RangeSubset(name = "Dox",
                                          values = [0.0, 10.0, 100.0]))
        
        self.wi = wi = WorkflowItem(operation = op,
                                    status = 'waiting',
                                    view_error = "Not yet plotted")
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        # run estimate
        op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        
    def testEstimate(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
        self.assertEqual(self.workflow.remote_eval("len(self.workflow[-1].operation._peaks[True])"), 2)
   
    def testChangeChannels(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.xchannel = "B1-A"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.ychannel = "V2-A"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testChangeScale(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.xscale = "log"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.yscale = "log"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
                
    def testChangeBy(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.by = ["Dox"]
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
                
    def testChangeParams(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.h = 3
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.h0 = 2
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
                
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.tol = 0.3
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.merge_dist = 3
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
           
    def testChangeSubset(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.subset_list[0].selected = ["A"]
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid', 60)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
                  
    def testPlot(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.current_view = self.wi.default_view
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

    def testDensityPlot(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.default_view.show_density = True
        self.wi.current_view = self.wi.default_view
        self.workflow.wi_waitfor(self.wi, 'view_error', '', 60)
   
    def testSerializeOp(self):
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
        code = "import cytoflow as flow\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
            
            for view in wi.views:
                code = code + view.get_notebook_code(i)
         
        code_locals = {}
        with self.assertWarns(util.CytoflowWarning):
            exec(code, locals = code_locals)
            
        nb_data = code_locals['ex_3'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        
        pd.testing.assert_frame_equal(nb_data, remote_data)

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestFlowPeaks.testChangeScale']
    unittest.main()
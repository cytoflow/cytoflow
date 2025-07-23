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
Created on Jan 4, 2018

@author: brian
'''
import os, unittest, tempfile
import pandas as pd
import cytoflow.utility as util

# needed for testing lambdas
from cytoflow import geom_mean, geom_sd  # @UnusedImport

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations import ThresholdWorkflowOp, ThresholdSelectionView
from cytoflowgui.workflow.views import HistogramPlotParams
from cytoflowgui.workflow.serialization import load_yaml, save_yaml
from cytoflowgui.workflow.subset import CategorySubset, RangeSubset


class TestThreshold(ImportedDataTest):

    def setUp(self):
        super().setUp()

        self.addTypeEqualityFunc(ThresholdWorkflowOp, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(ThresholdSelectionView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(HistogramPlotParams, 'assertHasTraitsEqual')

        self.op = op = ThresholdWorkflowOp()
        op.name = "Thresh"
        op.channel = "Y2-A"
        op.threshold = 1000

        self.wi = wi = WorkflowItem(operation = op,
                                    status = 'waiting',
                                    view_error = "Not yet plotted")

        self.view = view = wi.default_view
        view.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))

        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        self.wi.current_view = self.wi.default_view
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        self.workflow.wi_waitfor(wi, 'view_error', "")
        self.workflow.wi_waitfor(wi, 'status', "valid")

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
        
        
    def testChangeThreshold(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.threshold = 0
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
   
    def testChangeChannels(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channel = "B1-A"
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')

    def testChangeScale(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.scale = "log"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
 
    def testChangeName(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.name = "Dange"
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        
    def testHueFacet(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.huefacet = "Dox"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        
    def testSubset(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list.append(RangeSubset(name = "Dox",
                                                 values = [0.0, 10.0, 100.0]))

        self.view.subset_list[0].selected = ["A"]
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
        code = "import cytoflow as flow\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
            
            for view in wi.views:
                code = code + view.get_notebook_code(i)
         
        code_locals = {}
        exec(code, locals = code_locals)
            
        nb_data = code_locals['ex_3'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        
        pd.testing.assert_frame_equal(nb_data, remote_data)

           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestQuad.testApply']
    unittest.main()
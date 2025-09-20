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

# needed for testing lambdas
from cytoflow import geom_mean, geom_sd  # @UnusedImport

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations import ThresholdWorkflowOp, CategoryWorkflowOp, CategoryOpSubset
from cytoflowgui.workflow.serialization import load_yaml, save_yaml
from cytoflowgui.workflow.subset import BoolSubset

class TestCategory(ImportedDataTest):

    def setUp(self):
        super().setUp()

        self.addTypeEqualityFunc(CategoryWorkflowOp, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(CategoryOpSubset, 'assertHasTraitsEqual')

        op = ThresholdWorkflowOp()
        op.name = "Y2_high"
        op.channel = "Y2-A"
        op.threshold = 300

        wi = WorkflowItem(operation = op,
                          status = 'waiting',
                          view_error = "Not yet plotted")
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi        
        self.workflow.wi_waitfor(wi, 'status', "valid")
        
        op = ThresholdWorkflowOp()
        op.name = "Y2_really_high"
        op.channel = "Y2-A"
        op.threshold = 30000

        wi = WorkflowItem(operation = op,
                          status = 'waiting',
                          view_error = "Not yet plotted")
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi        
        self.workflow.wi_waitfor(wi, 'status', "valid")
        
        self.op = op = CategoryWorkflowOp()
        op.name = "BO"
        op.subsets_list = [CategoryOpSubset(subset_list = [BoolSubset(name = "Y2_high", selected_f = True)], category = "Low"),
                           CategoryOpSubset(subset_list = [BoolSubset(name = "Y2_really_high", selected_t = True)], category = "High")]
        op.default = "Medium"
        
        self.wi = wi = WorkflowItem(operation = op,
                               status = 'waiting',
                               view_error = "Not yet plotted")
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi        
        self.workflow.wi_waitfor(wi, 'status', "valid")

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
        
    def testEvents(self):
        self.assertEqual(self.workflow.remote_eval("self.workflow[-1].result.data.groupby('BO', observed = True).size()['Low']"), 55091)
        self.assertEqual(self.workflow.remote_eval("self.workflow[-1].result.data.groupby('BO', observed = True).size()['Medium']"), 4521)
        self.assertEqual(self.workflow.remote_eval("self.workflow[-1].result.data.groupby('BO', observed = True).size()['High']"), 388)  
 
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
        
        
    def testSerializeEmptyOp(self):
        fh, filename = tempfile.mkstemp()
        op = CategoryWorkflowOp()
        try:
            os.close(fh)
             
            save_yaml(op, filename)
            new_op = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
                      
        self.assertEqual(op, new_op,)
                      
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
         
        exec(code, globals(), locals())
        nb_data = locals()['ex_5'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        
        pd.testing.assert_frame_equal(nb_data, remote_data)

           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestQuad.testApply']
    unittest.main()
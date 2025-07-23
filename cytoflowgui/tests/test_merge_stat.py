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

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations import ChannelStatisticWorkflowOp, MergeStatisticsWorkflowOp
from cytoflowgui.workflow.operations.xform_stat import transform_functions
from cytoflowgui.workflow.serialization import load_yaml, save_yaml

# we need these to exec() code in testNotebook
from cytoflow import ci, geom_mean, geom_sd  # @UnusedImport
from numpy import mean, median, std  # @UnusedImport
from scipy.stats import sem  # @UnusedImport
from pandas import Series  # @UnusedImport

class TestMergeStat(ImportedDataTest):
    
    def setUp(self):
        super().setUp()
        
        self.addTypeEqualityFunc(MergeStatisticsWorkflowOp, 'assertHasTraitsEqual')

        op = ChannelStatisticWorkflowOp()
        
        op.name = "Count_1"
        op.channel = "Y2-A"
        op.function_name = "Count"
        op.by = ['Dox', 'Well']
        
        wi = WorkflowItem(operation = op)
        self.workflow.workflow.append(wi)        
        
        op = ChannelStatisticWorkflowOp()
        
        op.name = "Count_2"
        op.channel = "B1-A"
        op.function_name = "Count"
        op.by = ['Dox', 'Well']
        
        wi = WorkflowItem(operation = op)
        self.workflow.workflow.append(wi) 
        
        self.op = op = MergeStatisticsWorkflowOp()
        
        op.name = "Merged"
        op.statistic_1 = "Count_1"
        op.statistic_2 = "Count_2"
                
        self.wi = wi = WorkflowItem(operation = op,
                                    status = 'waiting',
                                    view_error = "Not yet plotted")        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi

        self.workflow.wi_waitfor(wi, 'status', "valid")

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
 
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
            
        nb_data = code_locals['ex_4'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
    
        pd.testing.assert_frame_equal(nb_data, remote_data)

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestXformStat.testNotebook']
    unittest.main()
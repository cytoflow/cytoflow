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
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import ChannelStatisticPlugin, TransformStatisticPlugin
from cytoflowgui.op_plugins.xform_stat import transform_functions
from cytoflowgui.subset import BoolSubset, CategorySubset
from cytoflowgui.serialization import load_yaml, save_yaml

# we need these to exec() code in testNotebook
from cytoflow import ci, geom_mean
from numpy import mean, median, std
from scipy.stats import sem
from pandas import Series

class TestXformStat(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = ChannelStatisticPlugin()
        op = plugin.get_operation()
        
        op.name = "Count"
        op.channel = "Y2-A"
        op.statistic_name = "Count"
        op.by = ['Dox', 'Well']
        
        wi = WorkflowItem(operation = op)
        self.workflow.workflow.append(wi)        
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 30))
        
        plugin = TransformStatisticPlugin()
        self.op = op = plugin.get_operation()
        
        op.name = "Mean"
        op.statistic = ("Count", "Count")
        op.statistic_name = "Count"
        op.by = ["Dox"]
        op.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
                
        self.wi = wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi

        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 30))

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   

    def testChangeBy(self):
        self.op.by = ["Dox", "Well"]

        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

    def testChangeSubset(self):
        self.op.subset_list[0].selected = ["A"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))


    def testAllFunctions(self):
        for fn in transform_functions:
            self.op.statistic_name = fn
            self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
            self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

 
    def testSerialize(self):
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
             
            save_yaml(self.op, filename)
            new_op = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
                      
        self.assertDictEqual(self.op.trait_get(self.op.copyable_trait_names()),
                             new_op.trait_get(self.op.copyable_trait_names()))
         
         
    def testNotebook(self):
        for fn in transform_functions:
            self.op.statistic_name = fn
            self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
            self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
            
            code = "from cytoflow import *\n"
            for i, wi in enumerate(self.workflow.workflow):
                code = code + wi.operation.get_notebook_code(i)
             
            exec(code)
            nb_data = locals()['ex_1'].data
            remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
            self.assertTrue((nb_data == remote_data).all().all())

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestXformStat.testNotebook']
    unittest.main()
#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.workflow.operations.channel_stat import summary_functions
from cytoflowgui.workflow.serialization import load_yaml, save_yaml

# we need these to exec() code in testNotebook
from cytoflow import ci, geom_mean
from numpy import mean, median, std
from scipy.stats import sem
from pandas import Series

class TestChannelStat(ImportedDataTest):
    
    def setUp(self):
        super().setUp()
        
        # the last operation in ImportedDataTest.setUp is a ChannelStatistic op
        self.wi = wi = self.workflow.workflow[-1]
        self.op = self.wi.operation
        self.workflow.selected = wi

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   
    def testChangeChannels(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channel = "V2-A"
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testChangeBy(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.by = ["Dox"]
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

    def testChangeSubset(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.subset_list[0].selected = ["A"]
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

    def testAllFunctions(self):
        for fn in summary_functions:
            self.workflow.wi_sync(self.wi, 'status', 'waiting')
            self.op.statistic_name = fn
            self.workflow.wi_waitfor(self.wi, 'status', 'valid')
            self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
   
 
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
        for fn in summary_functions:
            self.workflow.wi_sync(self.wi, 'status', 'waiting')
            self.op.statistic_name = fn
            self.workflow.wi_waitfor(self.wi, 'status', 'valid')
            self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

            code = "from cytoflow import *\n"
            for i, wi in enumerate(self.workflow.workflow):
                code = code + wi.operation.get_notebook_code(i)
             
            exec(code)
            nb_data = locals()['ex_2'].data
            remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
            
            pd.testing.assert_frame_equal(nb_data, remote_data)

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestChannelStat.testGeomSD']
    unittest.main()
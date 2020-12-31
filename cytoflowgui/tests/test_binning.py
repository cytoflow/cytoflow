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
import pandas as pd

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.op_plugins import BinningPlugin
from cytoflowgui.serialization import load_yaml, save_yaml

class TestBinning(ImportedDataTest):
    
    def setUp(self):
        super().setUp()

        plugin = BinningPlugin()
        self.op = op = plugin.get_operation()
        op.name = "Bin"
        op.channel = "V2-A"
        op.scale = "log"
        op.bin_width = 0.2
                
        self.wi = wi = WorkflowItem(operation = op,
                                    status = 'waiting',
                                    view_error = "Not yet plotted")
        self.view = wi.default_view = op.default_view()
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi

        self.workflow.wi_waitfor(wi, 'status', "valid")
        
    def testApply(self):
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
   
    def testChangeChannels(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channel = "Y2-A"
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        

    def testChangeScale(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.scale = "linear"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.bin_width = 1000
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testChangeBinWidth(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.bin_width = 0.1
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testChangeBinWidthText(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.bin_width = "0.1"
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
          
    def testPlot(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.current_view = self.wi.default_view
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.op.channel = "Y2-A"
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
                      
        self.assertDictEqual(self.op.trait_get(self.op.copyable_trait_names()),
                             new_op.trait_get(self.op.copyable_trait_names()))
         
         
    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
         
        exec(code)
        nb_data = locals()['ex_3'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        
        pd.testing.assert_frame_equal(nb_data, remote_data)

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestBinning.testPlot']
    unittest.main()

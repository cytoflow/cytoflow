'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import BinningPlugin
from cytoflowgui.subset import BoolSubset, CategorySubset
from cytoflowgui.serialization import load_yaml, save_yaml

class TestBinning(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = BinningPlugin()
        self.op = op = plugin.get_operation()
        
        op.name = "Bin"
        op.channel = "V2-A"
        op.scale = "log"
        op.bin_width = 0.2
                
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi

        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 10))

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   
    def testChangeChannels(self):
        self.op.channel = "Y2-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        

    def testChangeScale(self):
        self.op.scale = "linear"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        
        self.op.bin_width = 1000
         
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

        
    def testChangeBinWidth(self):
        self.op.bin_width = 0.1
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))         
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

        
    def testChangeBinWidthText(self):
        self.op.bin_width = "0.1"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))         
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))


          
    def testPlot(self):
        self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        
        self.op.channel = "Y2-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
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
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
         
        exec(code)
        nb_data = locals()['ex_1'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        self.assertTrue((nb_data == remote_data).all().all())

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestBinning.testChangeBinWidth']
    unittest.main()
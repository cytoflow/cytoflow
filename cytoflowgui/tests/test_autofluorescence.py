'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import TasbeTest, wait_for
from cytoflowgui.op_plugins import AutofluorescencePlugin, ThresholdPlugin
from cytoflowgui.subset import BoolSubset
from cytoflowgui.serialization import load_yaml, save_yaml

class TestAutofluorescence(TasbeTest):
    
    def setUp(self):
        TasbeTest.setUp(self)
        
        plugin = ThresholdPlugin()
        op = plugin.get_operation()
                
        op.name = "Morpho"
        op.channel = "FSC-A"
        op.threshold = 100000

        wi = WorkflowItem(operation = op)
        self.workflow.workflow.append(wi)        
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 30))
 
        plugin = AutofluorescencePlugin()
        self.op = op = plugin.get_operation()
        
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        op.blank_file = self.cwd + "/../../cytoflow/tests/data/tasbe/blank.fcs"
        op.channels = ["FITC-A", "Pacific Blue-A", "PE-Tx-Red-YG-A"]
        op.subset_list.append(BoolSubset(name = "Morpho"))
        op.subset_list[0].selected_t = True
        
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = self.op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = self.wi
          
        # run the estimate
        op.do_estimate = True
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 30))

    def testEstimate(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
  
    def testChangeChannels(self):
        self.op.channels = ["FITC-A"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
  
    def testChangeSubset(self):
        self.op.subset_list[0].selected_t = False
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
         
    def testPlot(self):
        self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
  

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
        nb_data = locals()['ex_2'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        self.assertTrue((nb_data == remote_data).all().all())

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestAutofluorescence.testNotebook']
    unittest.main()
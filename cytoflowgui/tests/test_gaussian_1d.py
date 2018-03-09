'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import GaussianMixture1DPlugin
from cytoflowgui.subset import BoolSubset, CategorySubset
from cytoflowgui.serialization import load_yaml, save_yaml

class TestGaussian1D(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = GaussianMixture1DPlugin()
        self.op = op = plugin.get_operation()
        
        op.name = "Gauss"
        op.channel = "V2-A"
        op.channel_scale = "logicle"
        op.num_components = 2
        
        op.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
        
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        # run estimate
        op.do_estimate = True
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 30))

    def testEstimate(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   
    def testChangeChannels(self):
        self.op.channel = "Y2-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        

    def testChangeScale(self):
        self.op.channel_scale = "log"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))


    def testChangeBy(self):
        self.op.by = ["Dox"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
    def testChangeComponents(self):
        self.op.num_components = 3
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

    def testChangeSigma(self):
        self.op.sigma = 1
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))      
         
   
    def testChangeSubset(self):
        self.op.subset_list[0].selected = ["A"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
          
          
    def testPlot(self):
        self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
    def testPlotFacets(self):
        self.op.by = ["Dox", "Well"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.view = self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.yfacet = ""
        self.view.huefacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
   
 
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
#     import sys;sys.argv = ['', 'TestGaussian1D.testPlotFacets']
    unittest.main()
'''
Created on Jan 4, 2018

@author: brian
'''
import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import ThresholdPlugin
from cytoflowgui.serialization import load_yaml, save_yaml
from cytoflowgui.subset import CategorySubset


class TestThreshold(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)


        plugin = ThresholdPlugin()
        self.op = op = plugin.get_operation()
        op.name = "Thresh"
        op.channel = "Y2-A"
        op.threshold = 1000

        self.wi = wi = WorkflowItem(operation = op)

        self.view = view = wi.default_view = op.default_view()
        view.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))

        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        self.wi.current_view = self.wi.default_view
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))        
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 130))

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
        
        
    def testChangeThreshold(self):
        self.op.threshold = 0
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 130))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
   
    def testChangeChannels(self):
        self.op.channel = "B1-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 130))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

    def testChangeScale(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))

        self.view.scale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
 
    def testChangeName(self):
        self.op.name = "Dresh"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 130))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
    def testHueFacet(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))

        self.view.huefacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        
    def testSubset(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))

        self.view.subset_list[0].selected = ["A"]
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
        nb_data = locals()['ex_1'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        self.assertTrue((nb_data == remote_data).all().all())

           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestQuad.testApply']
    unittest.main()
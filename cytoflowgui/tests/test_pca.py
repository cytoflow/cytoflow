'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import PCAPlugin
from cytoflowgui.op_plugins.pca import _Channel
from cytoflowgui.subset import CategorySubset
from cytoflowgui.serialization import load_yaml, save_yaml, traits_eq, traits_hash

class TestPCA(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = PCAPlugin()
        self.op = op = plugin.get_operation()
        
        op.name = "PCA"
        op.channels_list = [_Channel(channel = "V2-A", scale = "log"),
                            _Channel(channel = "V2-H", scale = "log"),
                            _Channel(channel = "Y2-A", scale = "log"),
                            _Channel(channel = "Y2-H", scale = "log")]
        op.num_components = 2
        
        op.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
        
        self.wi = wi = WorkflowItem(operation = op)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        # run estimate
        op.do_estimate = True
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 30))

    def testEstimate(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
        self.assertTrue(self.workflow.remote_eval("'PCA_1' in self.workflow[-1].result.channels"))
        self.assertTrue(self.workflow.remote_eval("'PCA_2' in self.workflow[-1].result.channels"))
        
    def testRemoveChannel(self):
        self.op.channels_list.pop()
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testAddChannel(self):
        self.op.channels_list.append(_Channel(channel = "B1-A", scale = "log"))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
   
    def testComponents(self):
        self.op.num_components = 3
        
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

    def testChangeScale(self):
        self.op.channels_list[0].scale = "logicle"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
    def testChangeWhiten(self):
        self.op.whiten = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
    def testChangeBy(self):
        self.op.by = ["Dox"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

    def testChangeSubset(self):
        self.op.subset_list[0].selected = ["A"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
   
    def testSerializeOp(self):

        _Channel.__eq__ = traits_eq
        _Channel.__hash__ = traits_hash
         
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
#     import sys;sys.argv = ['', 'TestPCA.testSerializeOp']
    unittest.main()
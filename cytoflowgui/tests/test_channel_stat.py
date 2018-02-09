'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import ChannelStatisticPlugin
from cytoflowgui.subset import BoolSubset, CategorySubset
from cytoflowgui.serialization import load_yaml, save_yaml

class TestChannelStat(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = ChannelStatisticPlugin()
        self.op = op = plugin.get_operation()
        
        op.name = "MeanByDox"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.Mean"
        op.by = ['Dox']
        op.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
                
        self.wi = wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi

        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 10))

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   
   
    def testChangeChannels(self):
        self.op.channel = "V2-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
    def testChangeBy(self):
        self.op.by = ["Dox", "Well"]

        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

    def testChangeSubset(self):
        self.op.subset_list[0].selected = ["A"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

    def testGeomSD(self):        
        self.op.statistic_name = "Geom.SD"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', None))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', None))


    def testAllFunctions(self):
        self.op.statistic_name = "Mean"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

        self.op.statistic_name = "Count"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.op.statistic_name = "Std.Dev"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.op.statistic_name = "Geom.SD"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.op.statistic_name = "SEM"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.op.statistic_name = "Geom.SEM"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.op.statistic_name = "Mean 95% CI"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

        self.op.statistic_name = "Geom.Mean 95% CI"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
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
#     import sys;sys.argv = ['', 'TestChannelStat.testGeomSD']
    unittest.main()
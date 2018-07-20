'''
Created on Jan 4, 2018

@author: brian
'''
import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import PolygonPlugin
from cytoflowgui.serialization import load_yaml, save_yaml
from cytoflowgui.subset import CategorySubset


class TestPolygon(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.wi = self.workflow.workflow[0]
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))

        plugin = PolygonPlugin()
        self.op = op = plugin.get_operation()
        op.name = "Poly"
        op.xchannel = "Y2-A"
        op.xscale = "logicle"
        op.ychannel = "V2-A"
        op.yscale = "logicle"
        op.vertices = [(23.411982294776319, 5158.7027015021222), 
                       (102.22182270573683, 23124.0588433874530), 
                       (510.94519955277201, 23124.0588433874530), 
                       (1089.5215641232173, 3800.3424832180476), 
                       (340.56382570202402, 801.98947404942271), 
                       (65.42597937575897, 1119.3133482602157)]
        
        self.wi = wi = WorkflowItem(operation = op)

        self.view = view = wi.default_view = op.default_view()
        view.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        self.wi.current_view = self.wi.default_view
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[-1].default_view.vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 130))

    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
        
   
    def testChangeChannels(self):
        self.op.xchannel = "B1-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 130))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.workflow.remote_exec("self.workflow[-1].default_view.vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

        self.op.ychannel = "Y2-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 130))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.workflow.remote_exec("self.workflow[-1].default_view.vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

    def testChangeScale(self):
        self.op.xscale = "log"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 130))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.workflow.remote_exec("self.workflow[-1].default_view.vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

        self.op.yscale = "log"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 130))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.workflow.remote_exec("self.workflow[-1].default_view.vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
 
    def testChangeName(self):
        self.op.name = "Dolly"
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
#     import sys;sys.argv = ['', 'TestPolygon.testSerialize']
    unittest.main()
'''
Created on Jan 4, 2018

@author: brian
'''
import unittest, tempfile, os

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.view_plugins import HistogramPlugin
from cytoflowgui.serialization import save_yaml, load_yaml

class Test(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.wi = wi = self.workflow.workflow[0]
        plugin = HistogramPlugin()
        self.view = view = plugin.get_view()
        view.channel = "Y2-A"
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = self.wi
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
    def testBaseHistogram(self):
        pass

    def testLogScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.scale = "log"
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

    def testLogicleScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.scale = "logicle"
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
    def testXfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        
    def testYfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


    def testXandYfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        
    def testHueFacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.huefacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


    def testHueScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.huefacet = "Dox"
        self.view.huescale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
    
        
    def testSubset(self):
        from cytoflowgui.subset import CategorySubset
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
    
        
    def testAll(self):

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.scale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.scale = "logicle"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = "Well"
        self.view.yfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.yfacet = ""
        self.view.huefacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.huefacet = "Dox"
        self.view.huescale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
     

        from cytoflowgui.subset import CategorySubset
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = ""
        self.view.yfacet = ""
        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        
    def testSerialize(self):
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
            
            save_yaml(self.view, filename)
            new_op = load_yaml(filename)
            
        finally:
            os.unlink(filename)
            
        self.maxDiff = None
                     
        self.assertDictEqual(self.view.trait_get(self.view.copyable_trait_names()),
                             new_op.trait_get(self.view.copyable_trait_names()))
        
           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testLogScale']
    unittest.main()
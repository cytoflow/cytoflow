'''
Created on Jan 4, 2018

@author: brian
'''
import unittest, tempfile, os

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.view_plugins import ParallelCoordinatesPlugin
from cytoflowgui.view_plugins.parallel_coords import _Channel
from cytoflowgui.serialization import save_yaml, load_yaml

class TestParallelCoords(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.wi = wi = self.workflow.workflow[0]
        self.wi.operation.events = 500
        
        plugin = ParallelCoordinatesPlugin()
        self.view = view = plugin.get_view()
        
        view.channels_list = [_Channel(channel = "B1-A", scale = "log"),
                              _Channel(channel = "V2-A", scale = "log"),
                              _Channel(channel = "Y2-A", scale = "log")]

        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = self.wi
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
    def testBase(self):
        pass

    def testChangeScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.channels_list[1].scale = "linear"
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

    def testChangeChannel(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.channels_list[1].channel = "FSC-A"
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
    def testAddChannel(self):

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.channels_list.append(_Channel(channel = "FSC-A", scale = "log"))
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

    def testRemoveChannel(self):

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.channels_list.append(_Channel(channel = "FSC-A", scale = "log"))
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.channels_list.pop()
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

    def testXfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        
    def testYfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


    def testXandYfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

    def testHueScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.huescale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
    
        
    def testSubset(self):
        from cytoflowgui.subset import CategorySubset
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
    
    def testNotebook(self):
        # smoke test
        
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
            
            for view in wi.views:
                code = code + view.get_notebook_code(i)
         
        exec(code)
        
    def testSerialize(self):
        
     
        def channel_eq(self, other):
            return self.channel == other.channel and self.scale == other.scale
          
        def channel_hash(self):
            return hash((self.channel, self.scale))
        
        _Channel.__eq__ = channel_eq
        _Channel.__hash__ = channel_hash
        
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
    import sys;sys.argv = ['', 'TestParallelCoords.testSerialize']
    unittest.main()
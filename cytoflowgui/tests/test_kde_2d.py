'''
Created on Jan 4, 2018

@author: brian
'''
import unittest, tempfile, os

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.view_plugins.kde_2d import Kde2DPlugin, Kde2DPlotParams
from cytoflowgui.serialization import save_yaml, load_yaml, traits_eq, traits_hash

class TestKde2D(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.wi = wi = self.workflow.workflow[0]
        plugin = Kde2DPlugin()
        self.view = view = plugin.get_view()
        view.xchannel = "V2-A"
        view.ychannel = "Y2-A"
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = self.wi
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
    def testBaseDensity(self):
        pass

    def testLogScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.yscale = "log"
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

    def testLogicleScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xscale = "logicle"
        
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
        
        
    def testHueFacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.huefacet = "Dox"
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
    
        
    def testAll(self):

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xscale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.yscale = "logicle"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = "Well"
        self.view.yfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.yfacet = ""
        self.view.huefacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.huefacet = "Dox"
        self.view.huescale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
     

        from cytoflowgui.subset import CategorySubset
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))

        self.view.xfacet = ""
        self.view.yfacet = ""
        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
    def testPlotParams(self):
        
        # Common params
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.title = "Title"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.xlabel = "X label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.ylabel = "Y label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.sharex = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.sharey = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.despine = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.legend = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

 
        ## KDE-specific params
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.min_quantile = 0.01
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
 
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.max_quantile = 0.90
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
 
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.shade = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
 
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.min_alpha = 0.2
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
 
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.max_alpha = 0.7
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
 
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.n_levels = 5
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
         
        for k in ["biw", "cos", "epa", "tri", "triw", "uni", "gau"]:
            self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
            self.view.plot_params.kernel = k
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        for bw in ["silverman", "scott"]:
            self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
            self.view.plot_params.bw = bw
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.gridsize = 50
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))   

        
    def testSerialize(self):
        Kde2DPlotParams.__eq__ = traits_eq
        Kde2DPlotParams.__hash__ = traits_hash
        
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
            
            save_yaml(self.view, filename)
            new_view = load_yaml(filename)
            
        finally:
            os.unlink(filename)
            
        self.maxDiff = None
                     
        self.assertDictEqual(self.view.trait_get(self.view.copyable_trait_names()),
                             new_view.trait_get(self.view.copyable_trait_names()))
        
        
    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
           
        exec(code) # smoke test
           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testAll']
    unittest.main()
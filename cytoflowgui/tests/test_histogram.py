'''
Created on Jan 4, 2018

@author: brian
'''
import unittest, tempfile, os

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.view_plugins.histogram import HistogramPlugin, HistogramPlotParams
from cytoflowgui.serialization import save_yaml, load_yaml, traits_eq, traits_hash

class TestHistogram(ImportedDataTest):

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
        
   
    def testPlotArgs(self):

        # BasePlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.title = "Title"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.xlabel = "X label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.ylabel = "Y label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.xfacet = ""
        self.view.huefacet = "Dox"
        self.view.plot_params.huelabel = "Hue label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.xfacet = "Dox"
        self.view.yfacet = ""
        self.view.huefacet = ""
        self.view.plot_params.col_wrap = 2
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
         
        for style in ['darkgrid', 'whitegrid', 'white', 'dark', 'ticks']:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
            self.view.plot_params.sns_style = style
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
            
        for context in ['poster', 'talk', 'poster', 'notebook', 'paper']:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
            self.view.plot_params.sns_context = context
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.legend = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.sharex = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.sharey = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.despine = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))


        # DataPlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.min_quantile = 0.01
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.max_quantile = 0.90
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
        # Data1DPlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.lim = (0, 1000)
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.orientation = "horizontal"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
        # Histogram
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.num_bins = 500
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.histtype = "step"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.histtype = "bar"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

        for linestyle in ['solid', 'dashed', 'dashdot', 'dotted', 'none']:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
            self.view.plot_params.linestyle = linestyle
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
            
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.linewidth = "5"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
            
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.density = True
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))                    

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.view.plot_params.alpha = 0.1
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30)) 
        
    def testSerialize(self):
        
        HistogramPlotParams.__eq__ = traits_eq
        HistogramPlotParams.__hash__ = traits_hash
        
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
        
    def testSerializeV1(self):
        HistogramPlotParams.__eq__ = traits_eq
        HistogramPlotParams.__hash__ = traits_hash
        
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
            
            save_yaml(self.view, filename, lock_versions = {HistogramPlotParams : 1})
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
        
        exec(code)  # smoke test

           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestHistogram.testPlotArgs']
    unittest.main()
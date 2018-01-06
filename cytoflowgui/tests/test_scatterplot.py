'''
Created on Jan 4, 2018

@author: brian
'''
import unittest

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.view_plugins import ScatterplotPlugin

class TestScatterplot(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        old_plot_calls = self.workflow.plot_calls
        self.wi = wi = self.workflow.workflow[0]
        plugin = ScatterplotPlugin()
        self.view = view = plugin.get_view()
        view.xchannel = "Y2-A"
        view.ychannel = "V2-A"
        wi.views.append(view)
        wi.current_view = view
        
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(wi.view_error, "")
        
    def testBase(self):
        pass

    def testLogScale(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.xscale = "log"
        self.view.yscale = "log"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

    def testLogicleScale(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.xscale = "logicle"
        self.view.yscale = "logicle"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")
        
    def testXfacet(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")
        
    def testYfacet(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

    def testXandYfacet(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")
        
    def testHueFacet(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.huefacet = "Dox"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

    def testHueScale(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.huefacet = "Dox"
        self.view.huescale = "log"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")       
        
    def testSubset(self):
        from cytoflowgui.subset import CategorySubset
        old_plot_calls = self.workflow.plot_calls
        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")     
        
    def testAll(self):

        old_plot_calls = self.workflow.plot_calls
        self.view.xscale = "log"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

        old_plot_calls = self.workflow.plot_calls
        self.view.yscale = "logicle"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

        old_plot_calls = self.workflow.plot_calls
        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")
        
        old_plot_calls = self.workflow.plot_calls
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

        old_plot_calls = self.workflow.plot_calls
        self.view.xfacet = "Well"
        self.view.yfacet = "Dox"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

        old_plot_calls = self.workflow.plot_calls
        self.view.yfacet = ""
        self.view.huefacet = "Dox"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

        old_plot_calls = self.workflow.plot_calls
        self.view.huescale = "log"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")       

        from cytoflowgui.subset import CategorySubset
        old_plot_calls = self.workflow.plot_calls

        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "") 
           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestScatterplot.testAll']
    unittest.main()
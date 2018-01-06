'''
Created on Jan 4, 2018

@author: brian
'''
import unittest

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.view_plugins import HistogramPlugin

class Test(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        old_plot_calls = self.workflow.plot_calls
        self.wi = wi = self.workflow.workflow[0]
        plugin = HistogramPlugin()
        self.view = view = plugin.get_view()
        view.channel = "Y2-A"
        wi.views.append(view)
        wi.current_view = view
        
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(wi.view_error, "")
        
    def testBaseHistogram(self):
        pass

    def testLogScale(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.scale = "log"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

    def testLogicleScale(self):
        old_plot_calls = self.workflow.plot_calls
        self.view.scale = "logicle"
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
        self.view.scale = "log"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")

        old_plot_calls = self.workflow.plot_calls
        self.view.scale = "logicle"
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
        self.view.huefacet = "Dox"
        self.view.huescale = "log"
        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "")       

        from cytoflowgui.subset import CategorySubset
        old_plot_calls = self.workflow.plot_calls
        self.view.xfacet = ""
        self.view.yfacet = ""
        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.workflow, 'plot_calls', lambda v: v > old_plot_calls, 5))
        self.assertEqual(self.wi.view_error, "") 
           
if __name__ == "__main__":
    import sys;sys.argv = ['', 'Test.testAll']
    unittest.main()
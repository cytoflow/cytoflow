#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Jan 4, 2018

@author: brian
'''
import unittest, os, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, wait_for, params_traits_comparator  # @UnresolvedImport
from cytoflowgui.view_plugins.scatterplot import SCATTERPLOT_MARKERS, ScatterplotPlugin, ScatterplotPlotParams
from cytoflowgui.serialization import load_yaml, save_yaml

class TestScatterplot(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.wi = wi = self.workflow.workflow[0]
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))

        plugin = ScatterplotPlugin()
        self.view = view = plugin.get_view()
        view.xchannel = "Y2-A"
        view.ychannel = "V2-A"
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = wi
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        
    def testBase(self):
        pass

    def testLogScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xscale = "log"
        self.view.yscale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


    def testLogicleScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xscale = "logicle"
        self.view.yscale = "logicle"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        
    def testXfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        
    def testYfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


    def testXandYfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        
    def testHueFacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.huefacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


    def testHueScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.huefacet = "Dox"
        self.view.huescale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
 
        
    def testSubset(self):
        from cytoflowgui.subset import CategorySubset
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
  
        
    def testAll(self):

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xscale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.yscale = "logicle"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = "Well"
        self.view.yfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.yfacet = ""
        self.view.huefacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.huescale = "log"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
       

        from cytoflowgui.subset import CategorySubset
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))

        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
    def testPlotArgs(self):

        # BasePlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.title = "Title"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.xlabel = "X label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.ylabel = "Y label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = ""
        self.view.huefacet = "Dox"
        self.view.plot_params.huelabel = "Hue label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = "Dox"
        self.view.yfacet = ""
        self.view.huefacet = ""
        self.view.plot_params.col_wrap = 2
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
         
        for style in ['darkgrid', 'whitegrid', 'white', 'dark', 'ticks']:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
            self.view.plot_params.sns_style = style
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
            
        for context in ['poster', 'talk', 'poster', 'notebook', 'paper']:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
            self.view.plot_params.sns_context = context
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.legend = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.sharex = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.sharey = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.despine = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))


        # DataPlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.min_quantile = 0.01
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.max_quantile = 0.90
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        # Data2DPlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.xlim = (0, 1000)
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.ylim = (0, 1000)
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 130))
        
        # Scatterplot params

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.alpha = 0.5
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.s = 5
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.marker = '+'
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
                                    
        for m in SCATTERPLOT_MARKERS:
            self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
            self.view.plot_params.marker = m
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

    def testSerialize(self):
        with params_traits_comparator(ScatterplotPlotParams):
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


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestScatterplot.testSerialize']
    unittest.main()

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
import unittest, tempfile, os

from traits.util.async_trait_wait import wait_for_condition

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.view_plugins.histogram_2d import Histogram2DPlugin, Histogram2DParams
from cytoflowgui.serialization import save_yaml, load_yaml, traits_eq, traits_hash

class TestHistogram2D(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.wi = wi = self.workflow.workflow[0]
        plugin = Histogram2DPlugin()
        self.view = view = plugin.get_view()
        view.xchannel = "V2-A"
        view.ychannel = "Y2-A"
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = self.wi
        
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
    def testBaseDensity(self):
        pass

    def testLogScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.yscale = "log"
        
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

    def testLogicleScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.xscale = "logicle"
        
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
    def testXfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.xfacet = "Dox"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        
    def testYfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.yfacet = "Well"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)


    def testXandYfacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        
    def testHueFacet(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.huefacet = "Dox"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)


    def testHueScale(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.huescale = "log"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
    
        
    def testSubset(self):
        from cytoflowgui.subset import CategorySubset
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
    
        
    def testAll(self):

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.xscale = "log"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.yscale = "logicle"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.xfacet = "Dox"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.yfacet = "Well"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.xfacet = "Well"
        self.view.yfacet = "Dox"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.yfacet = ""
        self.view.huefacet = "Dox"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)


        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.huefacet = "Dox"
        self.view.huescale = "log"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
     

        from cytoflowgui.subset import CategorySubset
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)

        self.view.xfacet = ""
        self.view.yfacet = ""
        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list[0].selected = ['A']

        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
    def testPlotParams(self):

        # BasePlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.title = "Title"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.xlabel = "X label"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.ylabel = "Y label"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.xfacet = ""
        self.view.huefacet = "Dox"
        self.view.plot_params.huelabel = "Hue label"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.xfacet = "Dox"
        self.view.yfacet = ""
        self.view.huefacet = ""
        self.view.plot_params.col_wrap = 2
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
         
        for style in ['darkgrid', 'whitegrid', 'white', 'dark', 'ticks']:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
            self.view.plot_params.sns_style = style
            wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
            
        for context in ['poster', 'talk', 'poster', 'notebook', 'paper']:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
            self.view.plot_params.sns_context = context
            wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.legend = False
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.sharex = False
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.sharey = False
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.despine = False
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)


        # DataPlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.min_quantile = 0.01
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.max_quantile = 0.90
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        # Data2DPlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.xlim = (0, 1000)
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.ylim = (0, 1000)
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        

        ## 2d histogram-specific params

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.gridsize = 25
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.smoothed = True
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.smoothed_sigma = 2
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        
    def testSerialize(self):
        Histogram2DParams.__eq__ = traits_eq
        Histogram2DParams.__hash__ = traits_hash
        
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
#     import sys;sys.argv = ['', 'TestHistogram2D.testSerialize']
    unittest.main()
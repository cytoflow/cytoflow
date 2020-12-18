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
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

from traits.util.async_trait_wait import wait_for_condition

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.op_plugins import GaussianMixture1DPlugin
from cytoflowgui.subset import CategorySubset, RangeSubset
from cytoflowgui.serialization import load_yaml, save_yaml

class TestGaussian1D(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = GaussianMixture1DPlugin()
        self.op = op = plugin.get_operation()
        
        op.name = "Gauss"
        op.channel = "V2-A"
        op.channel_scale = "logicle"
        op.num_components = 2
        
        op.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
        op.subset_list.append(RangeSubset(name = "Dox", values = [0, 10, 100]))
        
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        # run estimate
        op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)

    def testEstimate(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   
    def testChangeChannels(self):
        self.op.channel = "Y2-A"
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

    def testChangeScale(self):
        self.op.channel_scale = "log"
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))


    def testChangeBy(self):
        self.op.by = ["Dox"]
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testChangeComponents(self):
        self.op.num_components = 3
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

    def testChangeSigma(self):
        self.op.sigma = 1
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
         
   
    def testChangeSubset(self):
        self.op.subset_list[0].selected = ["A"]
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
          
    def testPlot(self):
        self.wi.current_view = self.wi.default_view
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
    def testPlotFacets(self):
        self.op.by = ["Dox", "Well"]
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        
        self.view = self.wi.current_view = self.wi.default_view
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.xfacet = "Dox"
        self.view.current_plot = "A"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 300)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.yfacet = "Well"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.yfacet = ""
        self.view.huefacet = "Well"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

    def testBar(self):
        
        self.op.by = ["Dox", "Well"]
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view = self.wi.current_view = self.wi.default_view
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 300)
  
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 300)
        self.view.plot_params.histtype = "bar"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 300)
        
    def testPlotArgs(self):
        
        self.op.by = ["Dox", "Well"]
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view = self.wi.current_view = self.wi.default_view
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

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
        
        # Data1DPlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.lim = (0, 1000)
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.orientation = "horizontal"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        # Histogram
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.num_bins = 500
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
   
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.histtype = "step"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
  
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.histtype = "bar"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
 
        for linestyle in ['dashed', 'solid', 'dashed', 'dashdot', 'dotted']:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
            self.view.plot_params.linestyle = linestyle
            wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
              
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.linewidth = "5"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
              
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.density = True
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
  
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.alpha = 0.1
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
  
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
    import sys;sys.argv = ['', 'TestGaussian1D.testEstimate']
    unittest.main()
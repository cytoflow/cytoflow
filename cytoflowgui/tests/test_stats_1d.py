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

import matplotlib, pandas
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.op_plugins import ChannelStatisticPlugin
from cytoflowgui.view_plugins.stats_1d import Stats1DPlugin, Stats1DPlotParams, LINE_STYLES
from cytoflowgui.view_plugins.scatterplot import SCATTERPLOT_MARKERS
from cytoflowgui.subset import CategorySubset
from cytoflowgui.serialization import load_yaml, save_yaml

from cytoflowgui.tests.test_base import ImportedDataTest, params_traits_comparator

class TestStats1D(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = ChannelStatisticPlugin()
        
        op = plugin.get_operation()
        op.name = "MeanByDox"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.SD"
        op.by = ['Dox', 'Well']

        wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        
        op = plugin.get_operation()
        op.name = "MeanByDox"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.Mean"
        op.by = ['Dox', 'Well']
        op.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
                
        self.wi = wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi

        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        
        plugin = Stats1DPlugin()
        self.view = view = plugin.get_view()
        view.statistic = ("MeanByDox", "Geom.Mean")
        view.variable = "Dox"
        view.huefacet = "Well"
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
  
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = wi
        
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)


    def testPlot(self):
        pass
     
 
    def testLogScale(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
  
        self.view.xscale = "log"
          
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

 
    def testLogicleScale(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
  
        self.view.xscale = "logicle"
          
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

    def testXfacet(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.huefacet = ""
        self.view.xfacet = "Well"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
 
         
    def testYfacet(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.huefacet = ""
        self.view.yfacet = "Well"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        
    def testErrorBars(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.error_statistic = ("MeanByDox", "Geom.SD")
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
    def testPlotArgs(self):
        
        # BasePlotParams

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
        self.view.plot_params.huelabel = "Hue label"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.xfacet = "Well"
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
        
        # Data1DPlotParams
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.lim = (0, 1000)
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.orientation = "horizontal"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        ## stats1d-specific params
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.variable_lim = (-1.0, 11.0)
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.alpha = 0.5
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.marker = "+"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
                                    
        for m in SCATTERPLOT_MARKERS[::-1]:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
            self.view.plot_params.marker = m
            wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
            
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.linestyle = "dashed"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
            
        for el in LINE_STYLES[::-1]:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
            self.view.plot_params.linestyle = el
            wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.capsize = 5
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
 
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.shade_error = True
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.view.plot_params.orientation = "vertical"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
 
    def testSerialize(self):
        with params_traits_comparator(Stats1DPlotParams):
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

    def testSerializeWorkflowItemV1(self):
        with params_traits_comparator(Stats1DPlotParams):
            fh, filename = tempfile.mkstemp()
            try:
                os.close(fh)

                save_yaml(self.view, filename, lock_versions = {WorkflowItem: 1,
                                                                pandas.Series : 1})
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
#     import sys;sys.argv = ['', 'TestStats1D.testSerialize']
#     import sys;sys.argv = ['', 'TestStats1D.testSerializeWorkflowItemV1']
    unittest.main()

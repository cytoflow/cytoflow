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

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, Base2DStatisticsViewTest, params_traits_comparator
from cytoflowgui.view_plugins.stats_2d import Stats2DPlugin, Stats2DPlotParams, LINE_STYLES
from cytoflowgui.view_plugins.scatterplot import SCATTERPLOT_MARKERS
from cytoflowgui.op_plugins import ChannelStatisticPlugin
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.subset import CategorySubset, RangeSubset
from cytoflowgui.serialization import load_yaml, save_yaml

class TestStats2D(ImportedDataTest, Base2DStatisticsViewTest):
    
    def setUp(self):
        super().setUp()
        
        stats_plugin = ChannelStatisticPlugin()

        stats_op_3 = stats_plugin.get_operation()
        stats_op_3.name = "MeanByDoxIP2"
        stats_op_3.channel = "B1-A"
        stats_op_3.statistic_name = "Geom.Mean"
        stats_op_3.by = ['Dox', 'IP']
        stats_op_3.subset_list.append(CategorySubset(name = "Well",
                                                     values = ['A', 'B']))
        stats_op_3.subset_list.append(RangeSubset(name = "Dox",
                                                  values = [1.0, 10.0, 100.0]))
        stats_op_3.subset_list.append(RangeSubset(name = "IP",
                                                  values = [1.0, 10.0]))

        stats_wi_3 = WorkflowItem(operation = stats_op_3,
                                  status = "waiting",
                                  view_error = "Not yet plotted")
        self.workflow.workflow.append(stats_wi_3)
        self.workflow.wi_waitfor(stats_wi_3, 'status', 'valid')
        
        stats_op_4 = stats_plugin.get_operation()
        stats_op_4.name = "SDByDoxIP2"
        stats_op_4.channel = "B1-A"
        stats_op_4.statistic_name = "Geom.SD"
        stats_op_4.by = ['Dox', 'IP']
        stats_op_4.subset_list.append(CategorySubset(name = "Well",
                                                     values = ['A', 'B']))
        stats_op_4.subset_list.append(RangeSubset(name = "Dox",
                                                  values = [1.0, 10.0, 100.0]))
        stats_op_4.subset_list.append(RangeSubset(name = "IP",
                                                  values = [1.0, 10.0]))
        
        stats_wi_4 = WorkflowItem(operation = stats_op_4,
                                  status = "waiting",
                                  view_error = "Not yet plotted")
        self.workflow.workflow.append(stats_wi_4)
        self.workflow.wi_waitfor(stats_wi_4, 'status', 'valid')
                
        self.wi = wi = self.workflow.workflow[-1]      

        plugin = Stats2DPlugin()
        self.view = view = plugin.get_view()
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = wi
        
        super().setUpView()


    def testPlot(self):
        pass


    def testPlotParams(self):

        super().testPlotParams()
        
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.alpha = 0.5
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.marker = "+"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
                                    
        for m in SCATTERPLOT_MARKERS[::-1]:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.marker = m
            self.workflow.wi_waitfor(self.wi, 'view_error', '')
            
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.linestyle = "dashed"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
            
        for el in LINE_STYLES[::-1]:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.linestyle = el
            self.workflow.wi_waitfor(self.wi, 'view_error', '')
            
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.capsize = 5
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

    def testSerialize(self):
        with params_traits_comparator(Stats2DPlotParams):
            fh, filename = tempfile.mkstemp()
            try:
                os.close(fh)

                save_yaml(self.view, filename)
                new_view = load_yaml(filename)
            finally:
                os.unlink(filename)

            self.maxDiff = None

            self.assertDictEqual(self.view.trait_get(self.view.copyable_trait_names(**{"status" : lambda t: t is not True})),
                                 new_view.trait_get(self.view.copyable_trait_names(**{"status" : lambda t: t is not True})))

    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
           
        exec(code) # smoke test


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestStats2D.testPlot']
    unittest.main()

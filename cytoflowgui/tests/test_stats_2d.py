#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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

# needed for testing lambdas
import pandas as pd  # @UnusedImport
from cytoflow import geom_mean, geom_sd  # @UnusedImport

from cytoflowgui.tests.test_base import ImportedDataTest, Base2DStatisticsViewTest
from cytoflowgui.workflow.views.stats_2d import Stats2DWorkflowView, Stats2DPlotParams, LINE_STYLES
from cytoflowgui.workflow.views.scatterplot import SCATTERPLOT_MARKERS
from cytoflowgui.op_plugins import ChannelStatisticPlugin
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.subset import CategorySubset, RangeSubset
from cytoflowgui.workflow.serialization import load_yaml, save_yaml

class TestStats2D(ImportedDataTest, Base2DStatisticsViewTest):
    
    def setUp(self):
        super().setUp()
        
        self.addTypeEqualityFunc(Stats2DWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(Stats2DPlotParams, 'assertHasTraitsEqual')
        
        stats_plugin = ChannelStatisticPlugin()

        stats_op_3 = stats_plugin.get_operation()
        stats_op_3.name = "MeanByDoxIP2"
        stats_op_3.channel = "B1-A"
        stats_op_3.function_name = "Geo.Mean"
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
        stats_op_4.function_name = "Geo.SD"
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

        self.view = view = Stats2DWorkflowView()
        wi.views.append(view)
        wi.current_view = view
        
        super().setUpView()

        self.workflow.selected = wi
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

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
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)

            save_yaml(self.view, filename)
            new_view = load_yaml(filename)
        finally:
            os.unlink(filename)

        self.maxDiff = None

        self.assertEqual(self.view, new_view)
                      
    def testSerializeWorkflowItem(self):
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
             
            save_yaml(self.wi, filename)
            new_wi = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
        
        self.assertEqual(self.wi, new_wi)
                
    def testNotebook(self):
        code = "import cytoflow as flow\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
            
            for view in wi.views:
                code = code + view.get_notebook_code(i)
           
        exec(code) # smoke test


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestStats2D.testPlot']
    unittest.main()

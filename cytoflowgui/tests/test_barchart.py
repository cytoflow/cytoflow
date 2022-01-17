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

from cytoflowgui.tests.test_base import ImportedDataTest, Base1DStatisticsViewTest
from cytoflowgui.workflow.views.bar_chart import BarChartWorkflowView, BarChartPlotParams
from cytoflowgui.workflow.serialization import load_yaml, save_yaml

class TestBarchart(ImportedDataTest, Base1DStatisticsViewTest):
    
    def setUp(self):
        super().setUp()
        
        self.addTypeEqualityFunc(BarChartWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(BarChartPlotParams, 'assertHasTraitsEqual')

        self.wi = wi = self.workflow.workflow[-1]        
        self.view = view = BarChartWorkflowView()
        wi.views.append(view)
        wi.current_view = view
    
        super().setUpView()
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
    
    def testBasePlot(self):
        pass
     
    def testPlotParams(self):
        super().testPlotParams()
 
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.errwidth = 2
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
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
           
            for view in wi.views:
                code = code + view.get_notebook_code(i)
                
        exec(code) # smoke test


if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestBarchart.testPlot']
    unittest.main()

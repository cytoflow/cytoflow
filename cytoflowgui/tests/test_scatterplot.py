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
Created on Jan 4, 2018

@author: brian
'''
import unittest, os, tempfile

# needed for testing lambdas
import pandas as pd # @UnusedImport
from cytoflow import geom_mean, geom_sd  # @UnusedImport

from cytoflowgui.tests.test_base import ImportedDataTest, Base2DViewTest
from cytoflowgui.workflow.views.scatterplot import SCATTERPLOT_MARKERS, ScatterplotWorkflowView, ScatterplotPlotParams
from cytoflowgui.workflow.serialization import load_yaml, save_yaml

class TestScatterplot(ImportedDataTest, Base2DViewTest):

    def setUp(self):
        super().setUp()

        self.addTypeEqualityFunc(ScatterplotWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(ScatterplotPlotParams, 'assertHasTraitsEqual')

        self.wi = wi = self.workflow.workflow[-1]
        self.view = view = ScatterplotWorkflowView()
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = wi
        
        super().setUpView()
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testBase(self):
        pass
    
    def testPlotParams(self):
        super().testPlotParams()
        
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.alpha = 0.5
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.s = 5
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.marker = '+'
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
                                    
        for m in SCATTERPLOT_MARKERS[::-1]:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.marker = m
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
        
        exec(code)  # smoke test
                
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestScatterplot.testSerialize']
    unittest.main()

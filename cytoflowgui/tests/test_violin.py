#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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

from cytoflowgui.tests.test_base import ImportedDataTest, Base1DViewTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations import RangeWorkflowOp, RangeSelectionView
from cytoflowgui.workflow.views import ViolinPlotWorkflowView, ViolinPlotParams
from cytoflowgui.workflow.serialization import save_yaml, load_yaml

class TestViolin(ImportedDataTest, Base1DViewTest):

    def setUp(self):
        super().setUp()

        self.addTypeEqualityFunc(ViolinPlotWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(ViolinPlotParams, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(RangeWorkflowOp, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(RangeSelectionView, 'assertHasTraitsEqual')
        
        self.op = op = RangeWorkflowOp()
        op.name = "Range"
        op.channel = "Y2-A"
        op.low = 100
        op.high = 1000

        self.wi = wi = WorkflowItem(operation = op,
                                    status = 'waiting',
                                    view_error = "Not yet plotted")
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi

        self.view = view = ViolinPlotWorkflowView()
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = self.wi
        
        self.view.variable = "Range"
        super().setUpView()
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testBase(self):
        pass
    
    def testPlotParams(self):
        super().testPlotParams()
        
        for bw in ['silverman', 'scott']:    
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.bw = bw
            self.workflow.wi_waitfor(self.wi, 'view_error', '')
            
        for sp in ['count', 'area', 'width']:    
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.scale_plot = sp
            self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.gridsize = 200
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
        for inner in ['quartile', 'box', None]:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.inner = inner
            self.workflow.wi_waitfor(self.wi, 'view_error', '')
            
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.split = True
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
        
        exec(code)  # smoke test

           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestViolin.testSerialize']
    unittest.main()

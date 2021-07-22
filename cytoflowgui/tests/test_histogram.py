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
from cytoflowgui.workflow.views import HistogramWorkflowView, HistogramPlotParams
from cytoflowgui.workflow.serialization import save_yaml, load_yaml

class TestHistogram(ImportedDataTest, Base1DViewTest):

    def setUp(self):
        super().setUp()

        self.addTypeEqualityFunc(HistogramWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(HistogramPlotParams, 'assertHasTraitsEqual')

        self.wi = wi = self.workflow.workflow[-1]        
        self.view = view = HistogramWorkflowView()     
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = self.wi
        
        super().setUpView()
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
                
    def testBaseHistogram(self):
        pass
        
   
    def testPlotParams(self):
        super().testPlotParams()

        # Histogram
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.num_bins = 500
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.histtype = "step"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.histtype = "bar"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        for linestyle in ['dotted', 'solid', 'dashed', 'dashdot', 'dotted']:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.linestyle = linestyle
            self.workflow.wi_waitfor(self.wi, 'view_error', '')
            
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.linewidth = "5"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
            
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.density = True
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.alpha = 0.1
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
          
    def testSerializeV1(self):
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)

            save_yaml(self.view, filename, lock_versions = {HistogramPlotParams : 1})
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
        
        exec(code)  # smoke test

           
if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestHistogram.testPlotArgs']
    unittest.main()

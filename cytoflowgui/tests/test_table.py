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
from cytoflow import geom_mean, geom_sd  # @UnusedImport
import pandas as pd # @UnusedImport

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations import ChannelStatisticWorkflowOp
from cytoflowgui.workflow.views.table import TableWorkflowView
from cytoflowgui.workflow.serialization import load_yaml, save_yaml
from cytoflowgui.workflow.views.view_base import BasePlotParams


class TestTable(ImportedDataTest):
    
    def setUp(self):
        super().setUp()

        self.addTypeEqualityFunc(TableWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(BasePlotParams, 'assertHasTraitsEqual')

        op = ChannelStatisticWorkflowOp()
        op.name = "MeanByDox"
        op.channel = "Y2-A"
        op.function_name = "Geo.Mean"
        op.by = ['Dox']

        wi = WorkflowItem(operation = op,
                          status = 'waiting',
                          view_error = "Not yet plotted")        
        self.workflow.workflow.append(wi)
        
        op = ChannelStatisticWorkflowOp()
        op.name = "MeanByDoxAndWell"
        op.channel = "Y2-A"
        op.function_name = "Geo.Mean"
        op.by = ['Dox', 'Well']
        
        self.wi = wi = WorkflowItem(operation = op,
                          status = 'waiting',
                          view_error = "Not yet plotted")        
        self.workflow.workflow.append(wi)
        
        self.workflow.selected = wi

        self.workflow.wi_waitfor(wi, 'status', "valid")
        
        self.view = view = TableWorkflowView()
        view.statistic = "MeanByDox"
        view.feature = "Y2-A"
        view.row_facet = "Dox"
        
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
  
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = wi
        
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def tearDown(self):
        fh, filename = tempfile.mkstemp()
        
        try:
            os.close(fh)
                
            self.view._export_data(self.view.result, self.view.feature, filename)
        finally:
            os.unlink(filename)


    def testRow(self):
        pass
    
    def testColumn(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.row_facet = ""
        self.view.column_facet = "Dox"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testSubRow(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.statistic = "MeanByDoxAndWell"
        self.view.feature = "Y2-A"
        self.view.row_facet = "Dox"
        self.view.subrow_facet = "Well"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testSubColumn(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.statistic = "MeanByDoxAndWell"
        self.view.feature = "Y2-A"
        self.view.row_facet = ""
        self.view.column_facet = "Dox"
        self.view.subcolumn_facet = "Well"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testSubRowRange(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.statistic = "MeanByDoxAndWell"
        self.view.feature = "Y2-A"

        self.view.row_facet = "Dox"
        self.view.subrow_facet = "Well"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testSubColumnRange(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.statistic = "MeanByDoxAndWell"
        self.view.feature = "Y2-A"

        self.view.row_facet = ""
        self.view.column_facet = "Dox"
        self.view.subcolumn_facet = "Well"
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
#     import sys;sys.argv = ['', 'TestTable.testColumn']
    unittest.main()

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
import os, unittest, tempfile
import pandas as pd

# needed for testing lambdas
from cytoflow import geom_mean, geom_sd  # @UnusedImport

from cytoflowgui.tests.test_base import ImportedDataTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations import PolygonWorkflowOp, PolygonSelectionView, PolygonPlotParams
from cytoflowgui.workflow.serialization import load_yaml, save_yaml
from cytoflowgui.workflow.subset import CategorySubset, RangeSubset


class TestPolygon(ImportedDataTest):

    def setUp(self):
        super().setUp()

        self.addTypeEqualityFunc(PolygonWorkflowOp, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(PolygonSelectionView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(PolygonPlotParams, 'assertHasTraitsEqual')

        self.op = op = PolygonWorkflowOp()
        op.name = "Poly"
        op.xchannel = "Y2-A"
        op.xscale = "logicle"
        op.ychannel = "V2-A"
        op.yscale = "logicle"
        op.vertices = [(23.411982294776319, 5158.7027015021222), 
                       (102.22182270573683, 23124.0588433874530), 
                       (510.94519955277201, 23124.0588433874530), 
                       (1089.5215641232173, 3800.3424832180476), 
                       (340.56382570202402, 801.98947404942271), 
                       (65.42597937575897, 1119.3133482602157)]
        
        self.wi = wi = WorkflowItem(operation = op,
                                    status = 'waiting',
                                    view_error = "Not yet plotted")

        self.view = view = wi.default_view
        view.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        self.wi.current_view = self.wi.default_view
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        
        
    def testApply(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   
    def testChangeChannels(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.xchannel = "B1-A"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.workflow.remote_exec("self.workflow[-1].default_view._vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.ychannel = "Y2-A"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.workflow.remote_exec("self.workflow[-1].default_view._vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

    def testChangeScale(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.xscale = "log"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.workflow.remote_exec("self.workflow[-1].default_view._vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.yscale = "log"
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.workflow.remote_exec("self.workflow[-1].default_view._vertices = [(23.411982294776319, 5158.7027015021222), (102.22182270573683, 23124.0588433874530), (510.94519955277201, 23124.0588433874530), (1089.5215641232173, 3800.3424832180476), (340.56382570202402, 801.98947404942271), (65.42597937575897, 1119.3133482602157)]")
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
 
    def testChangeName(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.name = "Dolly"
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testHueFacet(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.huefacet = "Dox"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testDensity(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.density = True
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
 
    def testSubset(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.subset_list.append(CategorySubset(name = "Well",
                                                    values = ['A', 'B']))
        self.view.subset_list.append(RangeSubset(name = "Dox",
                                                 values = [0.0, 10.0, 100.0]))
        self.view.subset_list[0].selected = ["A"]
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
 
    def testSerialize(self):
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
             
            save_yaml(self.op, filename)
            new_op = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
                      
        self.assertEqual(self.op, new_op,)
                      
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
        
    def testSerializeEmptyOp(self):
        fh, filename = tempfile.mkstemp()
        op = PolygonWorkflowOp()
        try:
            os.close(fh)
             
            save_yaml(op, filename)
            new_op = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
                      
        self.assertEqual(op, new_op,)

                                     
    def testNotebook(self):
        code = "import cytoflow as flow\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
            
            for view in wi.views:
                code = code + view.get_notebook_code(i)
         
        exec(code, globals(), locals())
             
        nb_data = locals()['ex_3'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        
        pd.testing.assert_frame_equal(nb_data, remote_data)
        
    def testSerializeDensity(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.density = True
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
             
            save_yaml(self.op, filename)
            new_op = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
                      
        self.assertEqual(self.op, new_op,)
                      
    def testSerializeWorkflowItemDensity(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.density = True
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
             
            save_yaml(self.wi, filename)
            new_wi = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
        
        self.assertEqual(self.wi, new_wi)
                                     
    def testNotebookDensity(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.density = True
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
        code = "import cytoflow as flow\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
            
            for view in wi.views:
                code = code + view.get_notebook_code(i)
         
        exec(code, globals(), locals())
             
        nb_data = locals()['ex_3'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        
        pd.testing.assert_frame_equal(nb_data, remote_data)

           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestPolygon.testSerialize']
    unittest.main()
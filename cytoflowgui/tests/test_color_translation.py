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
import pandas as pd

from traits.util.async_trait_wait import wait_for_condition

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import TasbeTest, params_traits_comparator
from cytoflowgui.op_plugins import ColorTranslationPlugin, ThresholdPlugin
from cytoflowgui.op_plugins.color_translation import _Control
from cytoflowgui.subset import BoolSubset
from cytoflowgui.serialization import load_yaml, save_yaml

class TestColorTranslation(TasbeTest):
    
    def setUp(self):
        TasbeTest.setUp(self)
        
        plugin = ThresholdPlugin()
        op = plugin.get_operation()
                
        op.name = "Morpho"
        op.channel = "FSC-A"
        op.threshold = 100000

        wi = WorkflowItem(operation = op)
        self.workflow.workflow.append(wi)        
        wait_for_condition(lambda v: v.status == 'applying', wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', wi, 'status', 30)
         
        plugin = ColorTranslationPlugin()
        self.op = op = plugin.get_operation()
        
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.rby_file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        op.controls_list = [_Control(from_channel = "Pacific Blue-A",
                                     to_channel = "FITC-A",
                                     file = self.rby_file)]
#         op.channels = ["FITC-A", "Pacific Blue-A", "PE-Tx-Red-YG-A"]
        op.subset_list.append(BoolSubset(name = "Morpho"))
        op.subset_list[0].selected_t = True
        
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = self.op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = self.wi
          
        # run the estimate
        op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        
    def testEstimate(self):
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
  
    def testAddChannel(self):
        self.op.controls_list.append(_Control(from_channel = "PE-Tx-Red-YG-A",
                                              to_channel = "FITC-A",
                                              file = self.rby_file))
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
          
    def testChangeMixtureModel(self):
        self.op.mixture_model = True
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
  
    def testChangeSubset(self):
        self.op.subset_list[0].selected_t = False
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

    def testPlotMixtureModel(self):
        self.op.mixture_model = True
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'invalid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        
        self.op.do_estimate = True
        wait_for_condition(lambda v: v.status == 'estimating', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'applying', self.wi, 'status', 30)
        wait_for_condition(lambda v: v.status == 'valid', self.wi, 'status', 30)
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
        self.wi.current_view = self.wi.default_view
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

    def testSerialize(self):
        with params_traits_comparator(_Control):
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
        nb_data = locals()['ex_2'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        
        pd.testing.assert_frame_equal(nb_data, remote_data)


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestColorTranslation.testSerialize']
    unittest.main()

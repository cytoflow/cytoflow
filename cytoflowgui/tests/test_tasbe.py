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
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile
import pandas as pd

from cytoflowgui.tests.test_base import TasbeTest
from cytoflowgui.workflow.workflow_item import WorkflowItem
from cytoflowgui.workflow.operations.tasbe import TasbeWorkflowOp, TasbeWorkflowView, BleedthroughControl, TranslationControl, BeadUnit
from cytoflowgui.workflow.subset import BoolSubset
from cytoflowgui.workflow.serialization import load_yaml, save_yaml

class TestTASBE(TasbeTest):
    
    def setUp(self):
        super().setUp()      

        self.addTypeEqualityFunc(TasbeWorkflowOp, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(TasbeWorkflowView, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(BleedthroughControl, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(TranslationControl, 'assertHasTraitsEqual')
        self.addTypeEqualityFunc(BeadUnit, 'assertHasTraitsEqual')

        self.op = op = TasbeWorkflowOp()
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        
        self.wi = wi = WorkflowItem(operation = op,
                                    status = 'waiting',
                                    view_error = "Not yet plotted")
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = self.wi
        
        op.channels = ["FITC-A", "Pacific Blue-A", "PE-Tx-Red-YG-A"]

        op.blank_file = self.cwd + "/../../cytoflow/tests/data/tasbe/blank.fcs"     
        
        op.bleedthrough_list = [BleedthroughControl(channel = "FITC-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/eyfp.fcs"),
                                BleedthroughControl(channel = "Pacific Blue-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/ebfp.fcs"),
                                BleedthroughControl(channel = "PE-Tx-Red-YG-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/mkate.fcs")]
        
        op.beads_name = "RCP-30-5A Lot AA01, AA02, AA03, AA04, AB01, AB02, AC01 & GAA01-R"
        op.beads_file = self.cwd + "/../../cytoflow/tests/data/tasbe/beads.fcs"
        op.beads_unit = "MEFL"
        
        op.do_color_translation = True
        op.to_channel = "FITC-A"
        
        self.op.translation_list[0].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        self.op.translation_list[1].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        
        op.subset_list.append(BoolSubset(name = "Morpho"))
        op.subset_list[0].selected_t = True
          
        # run the estimate
        op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        
    def testEstimate(self):
        pass
  
    def testChangeChannels(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channels = ["FITC-A", "Pacific Blue-A"]
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        self.assertTrue(len(self.op.translation_list) == 1)
        self.assertTrue(len(self.op.bleedthrough_list) == 2)

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))     

    def testChangeChannelsThenPlot(self):
        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.channels = ["FITC-A", "Pacific Blue-A"]
        self.workflow.wi_waitfor(self.wi, 'status', 'invalid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
        self.assertTrue(len(self.op.translation_list) == 1)
        self.assertTrue(len(self.op.bleedthrough_list) == 2)

        self.workflow.wi_sync(self.wi, 'status', 'waiting')
        self.op.do_estimate = True
        self.workflow.wi_waitfor(self.wi, 'status', 'valid')
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))     
        
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.current_view = self.wi.default_view
        self.wi.default_view.current_plot = "Autofluorescence"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.default_view.current_plot = "Bleedthrough"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.default_view.current_plot = "Bead Calibration"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
         
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.default_view.current_plot = "Color Translation"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

    def testPlot(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.current_view = self.wi.default_view
        self.wi.default_view.current_plot = "Autofluorescence"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.default_view.current_plot = "Bleedthrough"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.default_view.current_plot = "Bead Calibration"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
         
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.wi.default_view.current_plot = "Color Translation"
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

        self.assertEqual(self.op, new_op)
                      
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
        
        exec(code)

        nb_data = locals()['ex_2'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        pd.testing.assert_frame_equal(nb_data, remote_data)
        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestTASBE.testPlot']
    unittest.main()

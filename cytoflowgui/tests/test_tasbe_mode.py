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

import os, unittest, tempfile, shutil

from traits.util.async_trait_wait import wait_for_condition

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import WorkflowTest
from cytoflowgui.tasbe_calibration import (TasbeCalibrationOp, _BleedthroughControl, _Unit)

class TestTASBECalibrationMode(WorkflowTest):
    
    def setUp(self):
        WorkflowTest.setUp(self)
        
        self.op = op = TasbeCalibrationOp()        
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = self.op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = self.wi
        
        op.blank_file = self.cwd + "/../../cytoflow/tests/data/tasbe/blank.fcs"     
        op.fsc_channel = "FSC-A"
        op.ssc_channel = "SSC-A"
        
        op._polygon_op.vertices = [(72417, 499), 
                                   (74598, 1499), 
                                   (118743, 3376), 
                                   (216547, 6166), 
                                   (246258, 4543), 
                                   (237880, 1973), 
                                   (139102, 872), 
                                   (87822, 519)]
        
        op.channels = ["FITC-A", "Pacific Blue-A", "PE-Tx-Red-YG-A"]
        
        op.bleedthrough_list = [_BleedthroughControl(channel = "FITC-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/eyfp.fcs"),
                                _BleedthroughControl(channel = "Pacific Blue-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/ebfp.fcs"),
                                _BleedthroughControl(channel = "PE-Tx-Red-YG-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/mkate.fcs")]
        
        op.beads_name = "Spherotech RCP-30-5A Lot AG01, AF02, AD04 and AAE01"
        op.beads_file = self.cwd + "/../../cytoflow/tests/data/tasbe/beads.fcs"
        op.units_list = [_Unit(channel = "FITC-A", unit = "MEFL"),
                         _Unit(channel = "Pacific Blue-A", unit = "MEBFP"),
                         _Unit(channel = "PE-Tx-Red-YG-A", unit = "MEPTR")]
        
        op.do_color_translation = False
        op.output_directory = tempfile.mkdtemp()
          
        # run the estimate
        op.do_estimate = True
        wait_for_condition(lambda v: v, self.op, 'valid_model', 30)

        
    def tearDown(self):
        
        # setting the output files 
        self.op.input_files = [self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"]
        wait_for_condition(lambda v: v.status == 'Done converting!', self.op, 'status', 30)

        shutil.rmtree(self.op.output_directory)

        WorkflowTest.tearDown(self)


    def testEstimate(self):
        pass
  
    def testChangeChannels(self):
        self.op.channels = ["FITC-A", "Pacific Blue-A"]
        wait_for_condition(lambda v: v == False, self.op, 'valid_model', 30)
        self.assertTrue(len(self.op.units_list) == 2)
        self.assertTrue(len(self.op.bleedthrough_list) == 2)

        self.op.do_estimate = True
        wait_for_condition(lambda v: v == True, self.op, 'valid_model', 30)
        
    def testDoTranslation(self):
        self.op.to_channel = "FITC-A"
        self.op.do_color_translation = True
        
        wait_for_condition(lambda v: v == False, self.op, 'valid_model', 30)
        self.assertEqual(len(self.op.units_list), 1)
        self.assertEqual(self.op.units_list[0].channel, "FITC-A")
        self.assertEqual(self.op.units_list[0].unit, "MEFL")
        self.assertEqual(len(self.op.translation_list), 2)
        
        self.op.translation_list[0].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        self.op.translation_list[1].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"

        self.op.do_estimate = 1
        wait_for_condition(lambda v: v == True, self.op, 'valid_model', 30)
        

    def testPlot(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.wi.current_view = self.wi.default_view
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.wi.default_view.current_plot = "Autofluorescence"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.wi.default_view.current_plot = "Bleedthrough"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.wi.default_view.current_plot = "Bead Calibration"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)
        
        self.op.to_channel = "FITC-A"
        self.op.do_color_translation = True
        
        wait_for_condition(lambda v: v == False, self.op, 'valid_model', 30)
        
        self.op.translation_list[0].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        self.op.translation_list[1].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"

        self.op.do_estimate = 1
        wait_for_condition(lambda v: v == True, self.op, 'valid_model', 30)
        
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        wait_for_condition(lambda v: v.view_error == "waiting", self.wi, 'view_error', 30)
        self.wi.default_view.current_plot = "Color Translation"
        wait_for_condition(lambda v: v.view_error == "", self.wi, 'view_error', 30)

if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestTASBECalibrationMode.testEstimate']
    unittest.main()

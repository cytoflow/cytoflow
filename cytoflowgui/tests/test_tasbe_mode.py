'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile, shutil

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import WorkflowTest, wait_for
from cytoflowgui.tasbe_calibration import (TasbeCalibrationOp, 
    TasbeCalibrationView, _BleedthroughControl, _TranslationControl, _Unit)
from cytoflowgui.subset import BoolSubset
from cytoflowgui.serialization import load_yaml, save_yaml

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
        self.assertTrue(wait_for(op, 'valid_model', lambda v: v, 30))

        
    def tearDown(self):
        self.op.input_files = [self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 5))

        shutil.rmtree(self.op.output_directory)

        WorkflowTest.tearDown(self)


    def testEstimate(self):
        pass
  
    def testChangeChannels(self):
        self.op.channels = ["FITC-A", "Pacific Blue-A"]
        self.assertTrue(wait_for(self.op, 'valid_model', lambda v: not v, 5))
        self.assertTrue(len(self.op.units_list) == 2)
        self.assertTrue(len(self.op.bleedthrough_list) == 2)

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.op, 'valid_model', lambda v: v, 30))
        
    def testDoTranslation(self):
        self.op.to_channel = "FITC-A"
        self.op.do_color_translation = True
        
        self.assertTrue(wait_for(self.op, 'valid_model', lambda v: not v, 30))
        self.assertEqual(len(self.op.units_list), 1)
        self.assertEqual(self.op.units_list[0].channel, "FITC-A")
        self.assertEqual(self.op.units_list[0].unit, "MEFL")
        self.assertEqual(len(self.op.translation_list), 2)
        
        self.op.translation_list[0].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        self.op.translation_list[1].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"

        self.op.do_estimate = 1
        self.assertTrue(wait_for(self.op, 'valid_model', lambda v: v, 30))
        

    def testPlot(self):
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 10))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.default_view.current_plot = "Autofluorescence"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 10))

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.default_view.current_plot = "Bleedthrough"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 10))  

        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.default_view.current_plot = "Bead Calibration"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 10)) 
        
        self.op.to_channel = "FITC-A"
        self.op.do_color_translation = True
        
        self.assertTrue(wait_for(self.op, 'valid_model', lambda v: not v, 30))
        
        self.op.translation_list[0].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        self.op.translation_list[1].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"

        self.op.do_estimate = 1
        self.assertTrue(wait_for(self.op, 'valid_model', lambda v: v, 30))
        
        self.workflow.remote_exec("self.workflow[0].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.default_view.current_plot = "Color Translation"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 10)) 

if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestTASBECalibrationMode.testPlot']
    unittest.main()

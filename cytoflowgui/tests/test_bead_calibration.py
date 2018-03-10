'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import TasbeTest, wait_for
from cytoflowgui.op_plugins import BeadCalibrationPlugin
from cytoflowgui.op_plugins.bead_calibration import _Unit
from cytoflowgui.serialization import save_yaml, load_yaml, traits_eq, traits_hash
import cytoflowgui.op_plugins.bead_calibration  # @UnusedImport

class TestBeadCalibration(TasbeTest):
    
    def setUp(self):
        TasbeTest.setUp(self)
 
        plugin = BeadCalibrationPlugin()
        self.op = op = plugin.get_operation()
        
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        op.beads_name = "Spherotech RCP-30-5A Lot AG01, AF02, AD04 and AAE01"
        op.beads_file = self.cwd + "/../../cytoflow/tests/data/tasbe/beads.fcs"
        op.units_list = [_Unit(channel = "FITC-A", unit = "MEFL"),
                         _Unit(channel = "Pacific Blue-A", unit = "MEBFP")]
        
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = self.op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = self.wi
          
        # run the estimate
        op.do_estimate = True
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 5))

    def testEstimate(self):
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testTextParams(self):
        self.op.bead_peak_quantile = "75"
        self.op.bead_brightness_threshold = "95.0"
        self.op.bead_brightness_cutoff = "262000"
        
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

        
    def testRemoveChannel(self):
        self.op.units_list.pop()
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testAddChannel(self):
        self.op.units_list.append(_Unit(channel = "PE-Tx-Red-YG-A", unit = "MEPTR"))
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
        
    def testBeadQuantile(self):
        self.op.bead_peak_quantile = 75
        
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))

    def testBeadThreshold(self):
        self.op.bead_brightness_threshold = 95.0
        
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
      
    def testBeadCutoff(self):
        self.op.bead_brightness_cutoff = 262000
        
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 5))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is not None"))
                              
    def testPlot(self):
        self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
           

    def testSerialize(self):

        _Unit.__eq__ = traits_eq
        _Unit.__hash__ = traits_hash
        
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
        nb_data = locals()['ex_1'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        self.assertTrue((nb_data == remote_data).all().all())
        

if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestBeadCalibration.testSerialize']
    unittest.main()
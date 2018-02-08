'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile, shutil

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import TasbeTest, wait_for
from cytoflowgui.op_plugins import ThresholdPlugin, TasbePlugin
from cytoflowgui.op_plugins.tasbe import _BleedthroughControl, _TranslationControl
from cytoflowgui.subset import BoolSubset
from cytoflowgui.serialization import load_yaml, save_yaml

import cytoflow.utility as util

class TestTASBE(TasbeTest):
    
    def setUp(self):
        TasbeTest.setUp(self)
        
        plugin = ThresholdPlugin()
        op = plugin.get_operation()
                
        op.name = "Morpho"
        op.channel = "FSC-A"
        op.threshold = 100000

        wi = WorkflowItem(operation = op)
        self.workflow.workflow.append(wi)        
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 5))
        
        plugin = TasbePlugin()
        self.op = op = plugin.get_operation()        
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = self.op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = self.wi
        
        op.channels = ["FITC-A", "Pacific Blue-A", "PE-Tx-Red-YG-A"]

        op.blank_file = self.cwd + "/../../cytoflow/tests/data/tasbe/blank.fcs"     
        
        op.bleedthrough_list = [_BleedthroughControl(channel = "FITC-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/eyfp.fcs"),
                                _BleedthroughControl(channel = "Pacific Blue-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/ebfp.fcs"),
                                _BleedthroughControl(channel = "PE-Tx-Red-YG-A",
                                                     file = self.cwd + "/../../cytoflow/tests/data/tasbe/mkate.fcs")]
        
        op.beads_name = "Spherotech RCP-30-5A Lot AG01, AF02, AD04 and AAE01"
        op.beads_file = self.cwd + "/../../cytoflow/tests/data/tasbe/beads.fcs"
        op.beads_unit = "MEFL"
        
        op.to_channel = "FITC-A"
        
        self.op.translation_list[0].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        self.op.translation_list[1].file = self.cwd + "/../../cytoflow/tests/data/tasbe/rby.fcs"
        
        op.subset_list.append(BoolSubset(name = "Morpho"))
        op.subset_list[0].selected_t = True
          
        # run the estimate
        op.do_estimate = True
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 30))

    def testEstimate(self):
        pass
  
    def testChangeChannels(self):
        self.op.channels = ["FITC-A", "Pacific Blue-A"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'invalid', 5))
        self.assertTrue(len(self.op.units_list) == 2)
        self.assertTrue(len(self.op.bleedthrough_list) == 2)

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        

    def testPlot(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.current_view = self.wi.default_view
        self.wi.default_view.current_plot = "Autofluorescence"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.default_view.current_plot = "Bleedthrough"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))  

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.default_view.current_plot = "Bead Calibration"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30)) 
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
        self.wi.default_view.current_plot = "Color Translation"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30)) 

  
    def testSerialize(self):
        
    
        def bl_eq(self, other):
            return self.channel == other.channel \
                and self.file == other.file
        
        def bl_hash(self):
            return hash((self.channel, self.file))
        
        _BleedthroughControl.__eq__ = bl_eq
        _BleedthroughControl.__hash__ = bl_hash
        
    
        def tr_eq(self, other):
            return self.from_channel == other.from_channel \
                and self.to_channel == other.to_channel \
                and self.file == other.file
        
        def tr_hash(self):
            return hash((self.from_channel, self.to_channel, self.file))
        
        _TranslationControl.__eq__ = tr_eq
        _TranslationControl.__hash__ = tr_hash
        
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
        
        self.assertTrue((nb_data == remote_data).all().all())
        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestTASBE.testSerialize']
    unittest.main()
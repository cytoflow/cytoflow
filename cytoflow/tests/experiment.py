"""
Created on Feb 10, 2015

@author: brian
"""

import unittest

import cytoflow as flow
import fcsparser

class TestExperiment(unittest.TestCase):
    """
    Unit tests for Experiment
    """

    def setUp(self):
        import os
        cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.Experiment()
        self.ex.add_conditions({"time" : "float"})
        self.tube1 = fcsparser.parse(cwd + '/data/Plate01/RFP_Well_A3.fcs', 
                                     reformat_meta = True,
                                     channel_naming = "$PnN")
        self.tube2 = fcsparser.parse(cwd + '/data/Plate01/CFP_Well_A4.fcs',
                                     reformat_meta = True,
                                     channel_naming = "$PnN")
    
    def test_metadata_unique(self):
        self.ex.add_tube(self.tube1, {"time" : 10.0})
        with self.assertRaises(RuntimeError):
            self.ex.add_tube(self.tube2, {"time" : 10.0})
        
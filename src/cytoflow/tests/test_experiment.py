"""
Created on Feb 10, 2015

@author: brian
"""

import unittest

import FlowCytometryTools as fc
import synbio_flowtools as sf

class TestExperiment(unittest.TestCase):
    """
    Unit tests for Experiment
    """

    def setUp(self):
        self.ex = sf.Experiment()
        self.ex.add_conditions({"time" : "float"})
        self.tube1 = fc.FCMeasurement(ID='Test 1',
                                      datafile='data/Plate01/RFP_Well_A3.fcs')
        self.tube2 = fc.FCMeasurement(ID='Test 2', 
                                      datafile='data/Plate01/CFP_Well_A4.fcs')
    
    def test_metadata_unique(self):
        self.ex.add_tube(self.tube1, {"time" : 10.0})
        with self.assertRaises(RuntimeError):
            self.ex.add_tube(self.tube2, {"time" : 10.0})
        
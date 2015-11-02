'''
Created on Oct 30, 2015

@author: brian
'''

import unittest

import cytoflow as flow
import fcsparser

class TestExperiment(unittest.TestCase):
    """
    Unit tests for Experiment
    """

    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.Experiment()
        tube = fcsparser.parse(self.cwd + '/data/tasbe/rby.fcs', 
                               reformat_meta = True)
        self.ex.add_tube(tube, {})
        
        self.af_op = flow.AutofluorescenceOp(
                    blank_file = self.cwd + '/data/tasbe/blank.fcs',
                    channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"])

    def test_estimate(self):
        self.af_op.estimate(self.ex)
        
        self.assertAlmostEqual(self.af_op._af_median["FITC-A"], 3.480000019073486)
        self.assertAlmostEqual(self.af_op._af_median["Pacific Blue-A"], 12.800000190734863)
        self.assertAlmostEqual(self.af_op._af_median["PE-Tx-Red-YG-A"], 21.15999984741211)
        
        self.assertAlmostEqual(self.af_op._af_stdev["FITC-A"], 77.12065887451172)
        self.assertAlmostEqual(self.af_op._af_stdev["Pacific Blue-A"], 51.380287170410156)
        self.assertAlmostEqual(self.af_op._af_stdev["PE-Tx-Red-YG-A"], 117.84236145019531)
                

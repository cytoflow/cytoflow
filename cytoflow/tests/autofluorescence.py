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
        self.ex = flow.Experiment(metadata = {"name_meta" : "$PnN"})
        tube = fcsparser.parse(self.cwd + '/data/tasbe/blank.fcs', 
                               reformat_meta = True,
                               channel_naming = "$PnN")
        self.ex.add_tube(tube, {})
        
        self.op = flow.AutofluorescenceOp(
                    blank_file = self.cwd + '/data/tasbe/blank.fcs',
                    channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"])
        self.op.estimate(self.ex)

    def test_estimate(self):
        self.assertAlmostEqual(self.op._af_median["FITC-A"], 3.480000019073486)
        self.assertAlmostEqual(self.op._af_median["Pacific Blue-A"], 12.800000190734863)
        self.assertAlmostEqual(self.op._af_median["PE-Tx-Red-YG-A"], 21.15999984741211)
        
        self.assertAlmostEqual(self.op._af_stdev["FITC-A"], 77.12065887451172)
        self.assertAlmostEqual(self.op._af_stdev["Pacific Blue-A"], 51.380287170410156)
        self.assertAlmostEqual(self.op._af_stdev["PE-Tx-Red-YG-A"], 117.84236145019531)
                
    def test_apply(self):
        ex2 = self.op.apply(self.ex)
        
        import numpy as np
        self.assertAlmostEqual(np.median(ex2["FITC-A"]), 0.0)
        self.assertAlmostEqual(np.median(ex2["Pacific Blue-A"]), 0.0)
        self.assertAlmostEqual(np.median(ex2["PE-Tx-Red-YG-A"]), 0.0)
        
    def test_plot(self):
        self.op.default_view().plot(self.ex)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
        
'''
Created on Nov 15, 2015

@author: brian
'''
import unittest

import cytoflow as flow
import fcsparser

class TestBeads(unittest.TestCase):

    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.Experiment()
        tube = fcsparser.parse(self.cwd + '/data/tasbe/rby.fcs', 
                               reformat_meta = True,
                               channel_naming = "$PnN")
        self.ex.add_tube(tube, {})
        
        self.op = flow.BeadCalibrationOp(
                    units = {"PE-Tx-Red-YG-A" : "MEPTR"},
                    beads_file = self.cwd + '/data/tasbe/beads.fcs',
                    beads = flow.BeadCalibrationOp.BEADS["Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R"])
        self.op.estimate(self.ex)

    def testCalibrationFn(self):
        # the four "correct" values were determined using the Spherotech
        # linearization and QC spreadsheet from
        # http://www.spherotech.com/RCP-30-5a%20%20rev%20G.2.xls
        
        # 1. the beads file was plotted and the five brightest peaks' locations
        #    were determined manually
        
        # 2. IN THE MEPTR SHEET (which matches the PE-Tx-Red channel), the 
        #    peaks were converted to 256-relative-channel measurements using
        #    Table 4
        
        # 3. The 256 RCN measurements were copied to the normalization table.
        #    The MEPTR values were copied from the standard table (on the left.)
        
        # 4. The test values (100, 1000, 10000, 100000) were converted to
        #    256 RCN, and the converted values copied into the cross-calibration
        #    table.
         
        self.assertAlmostEqual(self.op._calibration_functions["PE-Tx-Red-YG-A"](100),
                               908.2389, delta = 0.1)
        
        self.assertAlmostEqual(self.op._calibration_functions["PE-Tx-Red-YG-A"](1000),
                               8992.904, delta = 1)
                               
        self.assertAlmostEqual(self.op._calibration_functions["PE-Tx-Red-YG-A"](10000),
                               89022.543, delta = 10)
                               
        self.assertAlmostEqual(self.op._calibration_functions["PE-Tx-Red-YG-A"](100000),
                               881251.765, delta = 100)
        
    def testApply(self):
        # this is just to make sure the code doesn't crash;
        # nothing about correctness.
        
        self.op.apply(self.ex)

    def testPlot(self):
        # this is to make sure the code doesn't crash;
        # nothing about correctness
        
        self.op.default_view().plot(self.ex)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
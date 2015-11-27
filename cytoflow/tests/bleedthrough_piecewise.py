'''
Created on Nov 16, 2015

@author: brian
'''
import unittest

import cytoflow as flow
import fcsparser

class Test(unittest.TestCase):


    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.Experiment(metadata = {"name_meta" : "$PnN"})
        tube = fcsparser.parse(self.cwd + '/data/tasbe/rby.fcs', 
                               reformat_meta = True,
                               channel_naming = "$PnN")
        self.ex.add_tube(tube, {})
        
        self.op = flow.BleedthroughPiecewiseOp(
                                 controls = {"FITC-A" : self.cwd + '/data/tasbe/eyfp.fcs',
                                             "PE-Tx-Red-YG-A" : self.cwd + '/data/tasbe/mkate.fcs'})
        
    def testRun(self):
        self.op.estimate(self.ex)
        self.op.apply(self.ex)
        self.op.default_view().plot(self.ex)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
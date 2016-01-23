'''
Created on Nov 16, 2015

@author: brian
'''
import unittest

import matplotlib
matplotlib.use('Agg')

import cytoflow as flow

class Test(unittest.TestCase):


    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/rby.fcs',
                                                   conditions = {})]).apply()        
        
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
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
        
        self.op = flow.BinningOp(name = "Bin",
                                 channel = "PE-Tx-Red-YG-A",
                                 bin_width = 0.1,
                                 scale = "log10",
                                 bin_count_name = "Bin_Count")

    def testApply(self):
        """Just run apply(); don't actually test functionality"""
        self.op.apply(self.ex)
        
    def testView(self):
        """Just run default_view().plot(); don't actually test functionality"""
        self.op.default_view().plot(self.ex)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
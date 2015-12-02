'''
Created on Dec 1, 2015

@author: brian
'''
import unittest
import os

import cytoflow as flow
import fcsparser

class Test(unittest.TestCase):
    
    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.Experiment(metadata = {"name_meta" : "$PnN"})
        tube = fcsparser.parse(self.cwd + '/data/tasbe/mkate.fcs', 
                               reformat_meta = True,
                               channel_naming = "$PnN")
        self.ex.add_tube(tube, {})
        
        self.op = flow.LogTransformOp(channels = ["FSC-A", "Pacific Blue-A"])

    def test_run(self):
        self.op.apply(self.ex)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
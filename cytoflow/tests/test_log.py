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
        self.ex = flow.ImportOp(conditions = {},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/mkate.fcs',
                                                   conditions = {})]).apply()
        
        self.op = flow.LogTransformOp(channels = ["FSC-A", "Pacific Blue-A"])

    def test_run(self):
        self.op.apply(self.ex)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
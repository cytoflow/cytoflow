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
        self.ex = flow.Experiment()
        tube = fcsparser.parse(self.cwd + '/data/tasbe/mkate.fcs', 
                               reformat_meta = True)
        self.ex.add_tube(tube, {})
        
        self.op = flow.ColorTranslationOp(
                  
                  blank_file = self.cwd + '/data/tasbe/blank.fcs',
                    channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"])
        self.af_op.estimate(self.ex)


    def tearDown(self):
        pass


    def testName(self):
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
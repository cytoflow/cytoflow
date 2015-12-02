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
        tube = fcsparser.parse(self.cwd + '/data/tasbe/mkate.fcs', 
                               reformat_meta = True,
                               channel_naming = "$PnN")
        self.ex.add_tube(tube, {})
        
        self.op = flow.ColorTranslationOp(
                        translation = {"PE-Tx-Red-YG-A" : "FITC-A",
                                       "Pacific Blue-A" : "FITC-A"},
                        controls = {("PE-Tx-Red-YG-A", "FITC-A") :
                                    self.cwd + '/data/tasbe/rby.fcs',
                                    ("Pacific Blue-A", "FITC-A") :
                                    self.cwd + '/data/tasbe/rby.fcs'},
                        mixture_model = True)
            
        self.op.estimate(self.ex)

    def test_apply(self):
        self.op.apply(self.ex)
    
    def test_plot(self):
        self.op.default_view().plot(self.ex)
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
import unittest

import fcsparser
import cytoflow as flow

class TestLogicle(unittest.TestCase):
    
    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
        tube1 = flow.Tube(file = self.cwd + 'RFP_Well_A3.fcs', conditions = {})
        import_op = flow.ImportOp(conditions = {},
                                  tubes = [tube1])
        self.ex = import_op.apply()

        
    def test_logicle_estimate(self):
        """
        Test the parameter estimator against the R implementation
        """
               
        el = flow.LogicleTransformOp()
        el.name = "Logicle"
        el.channels = ["Y2-A"]
        
        el.estimate(self.ex)

        # these are the values the R implementation gives
        self.assertAlmostEqual(el.A['Y2-A'], 0.0)
        self.assertAlmostEqual(el.W['Y2-A'], 0.533191950161284)
        
    ### TODO - test the estimator failure modes
        
    def test_logicle_apply(self):
        """
        Make sure the function applies without segfaulting
        """
        
        el = flow.LogicleTransformOp()
        el.name = "Logicle"
        el.channels = ['Y2-A']
        
        el.estimate(self.ex)
        ex2 = el.apply(self.ex)
        
    ### TODO - test the apply function error checking
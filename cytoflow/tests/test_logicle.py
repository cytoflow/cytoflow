import unittest

import fcsparser
import cytoflow as flow

class TestLogicle(unittest.TestCase):
    
    def setUp(self):
        import os
        cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.Experiment(metadata = {"name_meta" : "$PnN"})
        self.ex.add_conditions({"time" : "float"})
        self.tube1 = fcsparser.parse(cwd + '/data/Plate01/RFP_Well_A3.fcs',
                                     reformat_meta = True,
                                     channel_naming = "$PnN")
        self.tube2 = fcsparser.parse(cwd + '/data/Plate01/CFP_Well_A4.fcs',
                                     reformat_meta = True,
                                     channel_naming = "$PnN")
        self.ex.add_tube(self.tube1, {"time" : 10.0})
        #self.ex.add_tube(self.tube2, {"time" : 20.0})
        
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
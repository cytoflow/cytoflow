import unittest

import FlowCytometryTools as fc
import cytoflow as flow

class TestLogicle(unittest.TestCase):
    
    def setUp(self):
        self.ex = flow.Experiment()
        self.ex.add_conditions({"time" : "float"})
        self.tube1 = fc.FCMeasurement(ID='Test 1',
                                      datafile='data/Plate01/RFP_Well_A3.fcs')
        self.tube2 = fc.FCMeasurement(ID='Test 2', 
                                      datafile='data/Plate01/CFP_Well_A4.fcs')
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
        self.assertAlmostEqual(el.T['Y2-A'], 262144.0)
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
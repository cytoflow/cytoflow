'''
Created on Dec 1, 2015

@author: brian
'''
import unittest

import matplotlib
matplotlib.use('Agg')

import cytoflow as flow
import os

class Test(unittest.TestCase):

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"

        tube1 = flow.Tube(file = self.cwd + 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + 'CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        ex = import_op.apply()

        # this works so much better on transformed data
        logicle = flow.LogicleTransformOp()
        logicle.name = "Logicle transformation"
        logicle.channels = ['V2-A', 'Y2-A', 'B1-A']
        logicle.estimate(ex)
        self.ex = logicle.apply(ex)

        self.gate = flow.GaussianMixture1DOp(name = "Gauss",
                                             channel = "Y2-A",
                                             sigma = 0.5,
                                             posteriors = True)
        
    def testEstimate(self):
        self.gate.estimate(self.ex)
        self.assertAlmostEqual(self.gate._gmms[True].means_[0][0], 0.138241432978, places = 3)
        self.assertAlmostEqual(self.gate._gmms[True].means_[1][0], 0.618966640805, places = 3)
    
    def testEstimateBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[0][0], 0.14084352777, places = 3)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[1][0], 0.440063665988, places = 1)        
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[0][0], 0.133235845266, places = 3)
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[1][0], 0.618998444886, places = 3) 
        
    def testApply(self):
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size()["Gauss_1"], 6340, delta = 3)
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size()["Gauss_2"], 2497, delta = 3)
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size()["Gauss_None"], 11163, delta = 3)
        
    def testApplyBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_1", 1], 3959, delta = 3)
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_1", 10], 2345, delta = 3)

        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_2", 1], 16, delta = 3)
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_2", 10], 2490, delta = 3)
        
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_None", 1], 6025, delta = 3)        
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_None", 10], 5165, delta = 3)        

    
    def testPlot(self):
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex)
        
    def testPlotBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex)
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
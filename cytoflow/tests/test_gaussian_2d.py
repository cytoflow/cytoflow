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

        self.gate = flow.GaussianMixture2DOp(name = "Gauss",
                                             xchannel = "V2-A",
                                             ychannel = "Y2-A",
                                             sigma = 2.0,
                                             posteriors = True)

        
    def testEstimate(self):
        self.gate.estimate(self.ex)
        self.assertAlmostEqual(self.gate._gmms[True].means_[0][0], 0.22138141)
        self.assertAlmostEqual(self.gate._gmms[True].means_[0][1], 0.13820187)
        self.assertAlmostEqual(self.gate._gmms[True].means_[1][0], 0.23076572)
        self.assertAlmostEqual(self.gate._gmms[True].means_[1][1], 0.61884163)
    
    def testEstimateBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[0][0], 0.36238996)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[0][1], 0.14943463)        
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[1][0], 0.2097935)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[1][1], 0.14054966)
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[0][0], 0.16640887)
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[0][1], 0.1326335)        
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[1][0], 0.23073166)
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[1][1], 0.61821791)
    
    def testApply(self):
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex) 
                 
        self.assertEqual(ex2.data.groupby("Gauss").size()["Gauss_1"], 6153)
        self.assertEqual(ex2.data.groupby("Gauss").size()["Gauss_2"], 2395)
        self.assertEqual(ex2.data.groupby("Gauss").size()["Gauss_None"], 11452)
        
    def testApplyBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
         
        self.assertEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_1", 1], 2026)
        self.assertEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_1", 10], 2452)
 
        self.assertEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_2", 1], 3126)
        self.assertEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_2", 10], 2398)
         
        self.assertEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_None", 1], 4848)        
        self.assertEqual(ex2.data.groupby(["Gauss", "Dox"]).size()["Gauss_None", 10], 5150)        
    
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
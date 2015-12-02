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

        self.gate = flow.PolygonOp(name = "Polygon",
                                   xchannel = "V2-A",
                                   ychannel = "Y2-A",
                                   vertices = [(0, 0.6), (0.2, 0.8), 
                                               (0.4, 0.6), (0.2, 0.4)])
        
    def testGate(self):
        ex2 = self.gate.apply(self.ex)
        
        # how many events ended up in the gate?
        self.assertEqual(ex2.data.groupby("Polygon").size()[True], 4098)
        
    def testPlot(self):
        self.gate.default_view().plot(self.ex)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
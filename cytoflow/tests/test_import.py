'''
Created on Dec 1, 2015

@author: brian
'''
import unittest
import os
import cytoflow as flow

class Test(unittest.TestCase):
    
    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"

    def testImport(self):
        tube1 = flow.Tube(file = self.cwd + 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + 'CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        ex = import_op.apply()
        
    def testVoltage(self):
        # TODO - test that tubbes with different voltages throw an exception
        # ... and that if you pass ignore_v it succeeds
        pass
        
    def testMetadata(self):
        # TODO - test that tubes with duplicate metadata fails
        pass
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
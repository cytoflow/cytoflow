'''
Created on Dec 1, 2015

@author: brian
'''
import unittest
import os
import cytoflow as flow

class Test(unittest.TestCase):
    
    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))

    def testImport(self):
        tube1 = flow.Tube(file = self.cwd + '/data/Plate01/RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + '/data/Plate01/CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        ex = import_op.apply()
        
    def testChannels(self):
        tube1 = flow.Tube(file = self.cwd + '/data/Plate01/RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + '/data/tasbe/blank.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        with self.assertRaises(RuntimeError):
            ex = import_op.apply()
        pass
        
    def testMetadata(self):
        tube1 = flow.Tube(file = self.cwd + '/data/Plate01/RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + '/data/Plate01/CFP_Well_A4.fcs', conditions = {"Dox" : 10.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        with self.assertRaises(RuntimeError):
            ex = import_op.apply()
    

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
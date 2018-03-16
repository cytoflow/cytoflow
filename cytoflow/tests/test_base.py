'''
Created on Mar 7, 2018

@author: brian
'''

import unittest, os

import cytoflow as flow
        
class ImportedDataTest(unittest.TestCase):
    
    def setUp(self):

        from cytoflow import Tube
        
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
     
        tube1 = Tube(file = self.cwd + "CFP_Well_A4.fcs",
                     conditions = {"Dox" : 0.0, "Well" : 'A'})
     
        tube2 = Tube(file = self.cwd + "RFP_Well_A3.fcs",
                     conditions = {"Dox" : 10.0, "Well" : 'A'})

        tube3 = Tube(file = self.cwd + "YFP_Well_A7.fcs",
                     conditions = {"Dox" : 100.0, "Well" : 'A'})
         
        tube4 = Tube(file = self.cwd + "CFP_Well_B4.fcs",
                     conditions = {"Dox" : 0.0, "Well" : 'B'})
     
        tube5 = Tube(file = self.cwd + "RFP_Well_A6.fcs",
                     conditions = {"Dox" : 10.0, "Well" : 'B'})

        tube6 = Tube(file = self.cwd + "YFP_Well_C7.fcs",
                     conditions = {"Dox" : 100.0, "Well" : 'B'})

        tube7 = Tube(file = self.cwd + "CFP_Well_B4.fcs",
                     conditions = {"Dox" : 0.0, "Well" : 'C'})
     
        tube8 = Tube(file = self.cwd + "RFP_Well_A6.fcs",
                     conditions = {"Dox" : 10.0, "Well" : 'C'})

        tube9 = Tube(file = self.cwd + "YFP_Well_C7.fcs",
                     conditions = {"Dox" : 100.0, "Well" : 'C'})
        
        self.ex = flow.ImportOp(conditions = {"Dox" : "float", "Well" : "category"},
                                tubes = [tube1, tube2, tube3, 
                                         tube4, tube5, tube6,
                                         tube7, tube8, tube9]).apply()
                                
    def tearDown(self):
        import matplotlib.pyplot
        matplotlib.pyplot.close('all')


class TasbeTest(unittest.TestCase):
    
    def setUp(self):

        from cytoflow import Tube
             
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/tasbe/"
     
        tube = Tube(file = self.cwd + "rby.fcs")
        
        self.ex = flow.ImportOp(tubes = [tube])
        
        
    def tearDown(self):
        import matplotlib.pyplot
        matplotlib.pyplot.close('all')
        
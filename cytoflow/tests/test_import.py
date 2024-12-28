#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Dec 1, 2015

@author: brian
'''

import unittest
import os
import cytoflow as flow

class TestImport(unittest.TestCase):
    
    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))

    def testImport(self):
        tube1 = flow.Tube(file = self.cwd + '/data/Plate01/RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + '/data/Plate01/CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        import_op.apply()

    def testCategories(self):
        tube1 = flow.Tube(file = self.cwd + '/data/Plate01/RFP_Well_A3.fcs', conditions = {"Dox" : "one"})
        tube2 = flow.Tube(file= self.cwd + '/data/Plate01/CFP_Well_A4.fcs', conditions = {"Dox" : "two"})
        import_op = flow.ImportOp(conditions = {"Dox" : "category"},
                                  tubes = [tube1, tube2])
        import_op.apply()
        
    def testSameChannels(self):
        tube1 = flow.Tube(file = self.cwd + '/data/Plate01/RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + '/data/tasbe/blank.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        with self.assertRaises(RuntimeError):
            import_op.apply()
        
    def testMetadata(self):
        tube1 = flow.Tube(file = self.cwd + '/data/Plate01/RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + '/data/Plate01/CFP_Well_A4.fcs', conditions = {"Dox" : 10.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        with self.assertRaises(RuntimeError):
            import_op.apply()

    def testChooseChannels(self):
        tube1 = flow.Tube(file = self.cwd + '/data/Plate01/RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        
        ex = flow.ImportOp(conditions = {"Dox" : "float"},
                           tubes = [tube1],
                           channels = {'Y2-A' : "Yellow"}).apply()
                           
        self.assertTrue(ex.channels == ["Yellow"])
        with self.assertRaises(RuntimeError):
            flow.ImportOp(conditions = {"Dox" : "float"},
                          tubes = [tube1],
                          channels = {'Y2-B' : "Blue"}).apply()
                          
    def testAccuriC6(self):
        path = self.cwd + '/data/instruments/' + 'Accuri - C6.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()

    def testAttune(self):
        path = self.cwd + '/data/instruments/' + 'Applied Biosystems - Attune.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testFACSAriaII(self):
        path = self.cwd + '/data/instruments/' + 'BD - FACS Aria II.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testCyan(self):
        path = self.cwd + '/data/instruments/' + 'Beckman Coulter - Cyan.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testCytomicsLMD(self):
        path = self.cwd + '/data/instruments/' + 'Beckman Coulter - Cytomics FC500.LMD'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testGalliosLMD(self):
        path = self.cwd + '/data/instruments/' + 'Beckman Coulter - Gallios.LMD'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()    
        
    def testMoFloAstriosLinear(self):
        path = self.cwd + '/data/instruments/' + 'Beckman Coulter - MoFlo Astrios - linear settings.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testMoFloAstriosLog(self):
        path = self.cwd + '/data/instruments/' + 'Beckman Coulter - MoFlo Astrios - log settings.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testMoFlowXDP(self):
        path = self.cwd + '/data/instruments/' + 'Beckman Coulter - MoFlo XDP.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testCytekDxP10(self):
        path = self.cwd + '/data/instruments/' + 'Cytek DxP10.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testCytekXP5(self):
        path = self.cwd + '/data/instruments/' + 'Cytek xP5.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testCytekNL2000(self):
        path = self.cwd + '/data/instruments/' + 'Cytek NL-2000.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testGuavaMuse(self):
        path = self.cwd + '/data/instruments/' +  'Guava Muse.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testICytEclipse(self):
        path = self.cwd + '/data/instruments/' + 'iCyt - Eclipse.lmd'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testMilliporeGuava(self):
        path = self.cwd + '/data/instruments/' + 'Millipore - Guava.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testMiltenyiMACSQuant(self):
        path = self.cwd + '/data/instruments/' + 'Miltenyi Biotec - MACSQuant Analyzer.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testPartecCyFlow29(self):
        path = self.cwd + '/data/instruments/' + 'Partec - CyFlow v2.9.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testPartecPAS(self):
        path = self.cwd + '/data/instruments/' + 'Partec - PAS.FCS'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testStratedigmS1400(self):
        path = self.cwd + '/data/instruments/' + 'Stratedigm - S1400.fcs'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()
        
    def testSystemIILMD(self):
        path = self.cwd + '/data/instruments/' + 'System II listmode with extra info in bits D10-D15.LMD'
        import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
        import_op.apply()    
                    
    def testDataset(self):
        file = self.cwd + '/data/instruments/Guava Muse.fcs'
        ex1 = flow.ImportOp(tubes = [flow.Tube(file = file)],
                            data_set = 0).apply()
        
        ex2 = flow.ImportOp(tubes = [flow.Tube(file = file)],
                            data_set = 1).apply()
                            
        self.assertNotEqual(len(ex1), len(ex2))

        ex3 = flow.ImportOp(tubes = [flow.Tube(file = file)],
                            data_set = 2).apply()
                            
        self.assertNotEqual(len(ex2), len(ex3))

        
        ex4 = flow.ImportOp(tubes = [flow.Tube(file = file)],
                            data_set = 3).apply()
                            
        self.assertNotEqual(len(ex3), len(ex4))

                            
if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestImport.testCategories']
    unittest.main()

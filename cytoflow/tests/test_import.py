#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
                          
    def testManufacturers(self):
        files = ['Accuri - C6.fcs',
                 'Applied Biosystems - Attune.fcs',
                 'BD - FACS Aria II.fcs',
                 'Beckman Coulter - Cyan.fcs',
                 'Beckman Coulter - Cytomics FC500.LMD',
                 'Beckman Coulter - Gallios.LMD',
                 'Beckman Coulter - MoFlo Astrios - linear settings.fcs',
                 'Beckman Coulter - MoFlo Astrios - log settings.fcs',
                 'Beckman Coulter - MoFlo XDP.fcs',
                 'Cytek DxP10.fcs',
                 'Cytek xP5.fcs',
                 'iCyt - Eclipse.lmd',
                 'Millipore - Guava.fcs',
                 'Miltenyi Biotec - MACSQuant Analyzer.fcs',
                 'Partec - PAS.FCS',
                 'Stratedigm - S1400.fcs',
                 'System II listmode with extra info in bits D10-D15.LMD']
        
        for file in files:
            path = self.cwd + '/data/instruments/' + file
            import_op = flow.ImportOp(tubes = [flow.Tube(file = path)])
            import_op.apply()
    
if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestImport.testManufacturers']
    unittest.main()

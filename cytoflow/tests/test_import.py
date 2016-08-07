#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

class Test(unittest.TestCase):
    
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
                           channels = ['Y2-A']).apply()
                           
        self.assertTrue(ex.channels == ["Y2-A"])
        with self.assertRaises(RuntimeError):
            flow.ImportOp(conditions = {"Dox" : "float"},
                          tubes = [tube1],
                          channels = ['Y2-B']).apply()
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
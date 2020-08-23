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

class Test(unittest.TestCase):

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
        tube1 = flow.Tube(file = self.cwd + 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + 'CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        self.ex = import_op.apply()

        self.gate = flow.PolygonOp(name = "Polygon",
                                   xchannel = "V2-A",
                                   ychannel = "Y2-A",
                                   vertices = [(-95.86, 12436.45), 
                                               (116.29, 22530.75), 
                                               (767.63, 4873.08), 
                                               (101.64, 939.38), 
                                               (-266.93, 2914.59)])
        
    def testGate(self):
        ex2 = self.gate.apply(self.ex)
                
        # how many events ended up in the gate?
        self.assertEqual(ex2.data.groupby("Polygon").size()[True], 4126)
        
    def testPlot(self):
        self.gate.default_view().plot(self.ex)
        self.gate.density_view(huescale="log", color="red").plot(self.ex, gridsize=20)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

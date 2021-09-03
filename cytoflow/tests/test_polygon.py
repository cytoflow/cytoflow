#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
import cytoflow as flow
import pandas as pd
from .test_base import ImportedDataSmallTest


class Test(ImportedDataSmallTest):
    def setUp(self):
        super().setUp()
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
        
        self.assertIsInstance(ex2.data.index, pd.RangeIndex)
        
    def testPlot(self):
        self.gate.default_view().plot(self.ex)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

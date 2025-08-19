#!/usr/bin/env python3.11
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2025
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


import unittest
import cytoflow as flow
from .test_base import ImportedDataSmallTest

class TestHierarchy(ImportedDataSmallTest):
    def setUp(self):
        super().setUp()
        self.ex = flow.ThresholdOp(name = "Y2_high",
                                   channel = "Y2-A",
                                   threshold = 300).apply(self.ex)
        self.ex = flow.ThresholdOp(name = "B1_high",
                                   channel = "B1-A",
                                   threshold = 400).apply(self.ex)
        self.ex = flow.HierarchyOp(name = "Cell_Type",
                                   gates = [("Y2_high", True, "Y2_high"),
                                            ("B1_high", True, "B1_high")]).apply(self.ex)
        
    def testEvents(self):
        self.assertEqual(self.ex.data.groupby("Cell_Type", 
                                              observed = True).size()['Y2_high'], 4481)
        self.assertEqual(self.ex.data.groupby("Cell_Type", 
                                              observed = True).size()['B1_high'], 35)
        self.assertEqual(self.ex.data.groupby("Cell_Type", 
                                              observed = True).size()['Unknown'], 15484)        
        
    def testCategories(self):
        self.assertEqual(set(self.ex['Cell_Type'].cat.categories), 
                         set(['B1_high', 'Unknown', 'Y2_high']))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
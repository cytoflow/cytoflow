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
import cytoflow.utility as util
from .test_base import ImportedDataSmallTest

class TestCategory(ImportedDataSmallTest):
    def setUp(self):
        super().setUp()
        self.ex = flow.ThresholdOp(name = "Y2_high",
                                   channel = "Y2-A",
                                   threshold = 300).apply(self.ex)
        self.ex = flow.ThresholdOp(name = "Y2_really_high",
                                   channel = "Y2-A",
                                   threshold = 30000).apply(self.ex)

        
    def testEvents(self):
        ex = flow.CategoryOp(name = "BO",
                           subsets = {"Y2_high == False" : "Low",
                                      "Y2_really_high == True" : "High"},
                           default = "Medium").apply(self.ex)
                           
        self.assertEqual(ex.data.groupby("BO", observed = True).size()['Low'], 15519)
        self.assertEqual(ex.data.groupby("BO", observed = True).size()['Medium'], 4480)
        self.assertEqual(ex.data.groupby("BO", observed = True).size()['High'], 1)        
        
    def testOverlappingSubsets(self):
        op = flow.CategoryOp(name = "BO",
                           subsets = {"Y2_high == True" : "Low",
                                      "Y2_really_high == True" : "High"},
                           default = "Medium")
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
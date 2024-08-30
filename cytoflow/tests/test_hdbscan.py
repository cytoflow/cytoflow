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
Created on April 27, 2023

@author: florian
'''
import unittest
import cytoflow as flow
import pandas as pd
from .test_base import ImportedDataTest

class TestHDBSCAN(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.op = flow.HDBSCANOp(name = "cluster",
                                channels = ["V2-A", "Y2-A"],
                                scale = {"V2-A" : "logicle",
                                         "Y2-A" : "logicle"})
        
    def testEstimate(self):
        self.op.estimate(self.ex)
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['cluster'].unique()), 4)
        
        self.assertIsInstance(ex2.data.index, pd.RangeIndex)
        
    def testEstimateBy(self):
        self.op.by = ["Well"]
        self.op.estimate(self.ex)
        
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['cluster'].unique()), 12)

    def testEstimateBy2(self):
        self.op.by = ["Well", "Dox"]
        self.op.estimate(self.ex)
        
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['cluster'].unique()), 6)

if __name__ == "__main__":
    unittest.main()

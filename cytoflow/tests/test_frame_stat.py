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
import cytoflow as flow
import pandas as pd
import cytoflow.utility as util
from .test_base import ImportedDataTest


class Test(ImportedDataTest):

    def setUp(self):
        super().setUp()
        self.ex = flow.ThresholdOp(name = "T",
                                   channel = "Y2-A",
                                   threshold = 500).apply(self.ex)
        
    def testApply(self):
        ex = flow.FrameStatisticOp(name = "ByDox",
                                   by = ['Dox', 'T'],
                                   function = lambda x: pd.Series({'Y2-A' : x['Y2-A'].mean(),
                                                                   'V2-A' : x['V2-A'].mean()})).apply(self.ex)
                                     
        self.assertIn("ByDox", ex.statistics)

        stat = ex.statistics["ByDox"]
        self.assertIn("Dox", stat.index.names)
        self.assertIn("T", stat.index.names)
        self.assertEqual(stat.columns.to_list(), ["Y2-A", "V2-A"])
                
        self.assertIsInstance(ex.data.index, pd.RangeIndex)
        
    def testSubset(self):
        op = flow.FrameStatisticOp(name = "ByDox",
                                   by = ['Dox', 'T'],
                                   subset = "Dox == 10.0",
                                   function = lambda x: pd.Series({'Y2-A' : x['Y2-A'].mean(),
                                                                   'V2-A' : x['V2-A'].mean()}))
        
        with self.assertWarns(util.CytoflowOpWarning):
            ex = op.apply(self.ex)

        stat = ex.statistics["ByDox"]
        
        self.assertEqual(stat.index.to_list(), [(10.0, False), (10.0, True)])
        self.assertEqual(stat.columns.to_list(), ["Y2-A", "V2-A"])
        
    def testBadFunction(self):
        
        op = flow.FrameStatisticOp(name = "ByDox",
                                   by = ['T'],
                                   subset = "Dox == 10.0",
                                   function = lambda x: len(x) / 0.0)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)



if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testSubset']
    unittest.main()

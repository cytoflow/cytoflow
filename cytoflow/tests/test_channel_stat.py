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
from .test_base import ImportedDataSmallTest


class TestChannelStats(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.ex = flow.ThresholdOp(name = "T",
                                   channel = "Y2-A",
                                   threshold = 500).apply(self.ex)
        
    def testApply(self):
        ex = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['Dox', 'T'],
                                     channel = "Y2-A",
                                     function = len).apply(self.ex)
                                     
        self.assertIn("ByDox", ex.statistics)

        stat = ex.statistics["ByDox"]
        self.assertIn("Dox", stat.index.names)
        self.assertIn("T", stat.index.names)
        
        self.assertIsInstance(ex.data.index, pd.RangeIndex)        
        
    def testApplySeries(self):
        ex = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['Dox', 'T'],
                                     channel = "Y2-A",
                                     function = lambda x: pd.Series({'Mean' : x.mean(),
                                                                     'SD' : x.std()})).apply(self.ex)
        
        stat = ex.statistics["ByDox"]
        self.assertTrue('Mean' in stat.columns)
        self.assertTrue('SD' in stat.columns)
        
    def testSubset(self):
        ex = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = len).apply(self.ex)
        stat = ex.statistics["ByDox"]
        self.assertEqual(stat.at[(False,), "Y2-A"], 5601)
        self.assertEqual(stat.at[(True,), "Y2-A"], 4399)
        
    def testBadFunction(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = lambda x: len(x) / 0.0)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testNoName(self):
        op = flow.ChannelStatisticOp(by = ['T'],
                                     channel = "Y2-A",
                                     function = len)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testBadName(self):
        op = flow.ChannelStatisticOp(name = "ByDox!",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     function = len)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testNoChannel(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     function = len)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testBadChannel(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-Z",
                                     function = len)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testNoFunction(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A")
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testStatExists(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     function = len)
        ex2 = op.apply(self.ex)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(ex2)
            
    def testNoBy(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     channel = "Y2-A",
                                     function = len)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testBadSubset(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox is weird",
                                     function = lambda x: len(x) / 0.0)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testZeroSubset(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 50.0",
                                     function = lambda x: len(x))
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testBadBy(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['derp'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = lambda x: len(x))
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testBadRedType(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = lambda _: 'a')
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testInconstFunction(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = lambda x: 0.0 if len(x) > 5000 else pd.Series([0.0, 1.0]))
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testBadSeries(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = lambda _: pd.Series(['a', 'b', 'c']))
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testNaN(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = lambda _: pd.Series([1.0, 0.0, float('nan')]))
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)
            
    def testOneSubset(self):
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['Dox'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = lambda x: len(x))
        
        with self.assertWarns(util.CytoflowOpWarning):
            op.apply(self.ex)
    #
    # def testBadSet(self):
    #
    #     self.ex = flow.ChannelStatisticOp(name = "Y_bad",
    #                                       channel = "Y2-A",
    #                                       by = ['Well'],
    #                                       function = flow.geom_sd_range).apply(self.ex)
                             


if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestChannelStats.testTuple']
    unittest.main()

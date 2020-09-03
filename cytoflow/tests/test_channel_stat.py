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

import os
import unittest

import cytoflow as flow
import cytoflow.utility as util

from test_base import ImportedDataTest  # @UnresolvedImport

class TestChannelStats(unittest.TestCase):
    
    def setUp(self):
        ImportedDataTest.setUp(self)
        
        self.ex = flow.ThresholdOp(name = "T",
                                   channel = "Y2-A",
                                   threshold = 500).apply(self.ex)
        
    def testApply(self):
        ex = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['Dox', 'T'],
                                     channel = "Y2-A",
                                     function = len).apply(self.ex)
                                     
        self.assertIn(("ByDox","len"), ex.statistics)

        stat = ex.statistics[("ByDox", "len")]
        self.assertIn("Dox", stat.index.names)
        self.assertIn("T", stat.index.names)
        
    def testSubset(self):
        ex = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = len).apply(self.ex)
        stat = ex.statistics[("ByDox", "len")]
       
        self.assertEqual(stat.loc[False].values[0], 24801)
        self.assertEqual(stat.loc[True].values[0], 5199)
        
    def testBadFunction(self):
        
        op = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['T'],
                                     channel = "Y2-A",
                                     subset = "Dox == 10.0",
                                     function = lambda x: len(x) / 0.0)
        
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)

    def testBadSet(self):
                             
        self.ex = flow.ChannelStatisticOp(name = "Y_bad",
                             channel = "Y2-A",
                             by = ['Well'],
                             function = flow.geom_sd_range).apply(self.ex)
                             


if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestChannelStats.testBadSet']
    unittest.main()
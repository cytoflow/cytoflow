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
import pandas as pd

import cytoflow as flow
import cytoflow.utility as util
from test_base import ImportedDataSmallTest


class Test(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.ex = flow.ThresholdOp(name = "T",
                                   channel = "Y2-A",
                                   threshold = 500).apply(self.ex)
                                   
        self.ex = flow.ChannelStatisticOp(name = "ByDox",
                                          by = ['Dox', 'T'],
                                          channel = "Y2-A",
                                          function = len).apply(self.ex)
        
    def testApply(self):
        ex = flow.TransformStatisticOp(name = "ByDox",
                                       statistic = ("ByDox", "len"),
                                       by = ['Dox'],
                                       statistic_name = "sum",
                                       function = lambda x: x.sum()).apply(self.ex)
                                     
        self.assertIn(("ByDox","sum"), ex.statistics)
 
        stat = ex.statistics[("ByDox", "sum")]
        
        self.assertIn("Dox", stat.index.names)
        self.assertNotIn("T", stat.index.names)

    def testBadFunction(self):
         
        op = flow.TransformStatisticOp(name = "ByDox",
                                       by = ['Dox'],
                                       statistic = ("ByDox", "len"),
                                       function = lambda x: (len(x) / 0.0))
         
        with self.assertRaises(util.CytoflowOpError):
            op.apply(self.ex)

    def testSeries(self):      
        op = flow.TransformStatisticOp(name = "ByDox",
                                       by = ['Dox'],
                                       statistic = ("ByDox", "len"),
                                       function = lambda x: (x / x.sum()),
                                       statistic_name = "prop")
        
        ex2 = op.apply(self.ex)
        stat = ex2.statistics[("ByDox", "prop")]
         
        self.assertIsInstance(stat, pd.Series)
        self.assertIsNot(type(stat.iloc[0]), pd.Series)


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testApply']
    unittest.main()

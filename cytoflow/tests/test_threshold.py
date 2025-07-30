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
from .test_base import ImportedDataSmallTest


class Test(ImportedDataSmallTest):
    def setUp(self):
        super().setUp()
        self.gate = flow.ThresholdOp(name = "Threshold",
                                     channel = "Y2-A",
                                     threshold = 500)
        
    def testGate(self):
        ex2 = self.gate.apply(self.ex)
        
        # how many events ended up in the gate?
        self.assertEqual(ex2.data.groupby("Threshold", observed = True).size()[True], 4446)
        
        self.assertIsInstance(ex2.data.index, pd.RangeIndex)

    def testPlot(self):
        self.gate.default_view().plot(self.ex)

    def testPlotWithSubset(self):
        self.gate.default_view(subset = "Dox == 10.0").plot(self.ex)
        
    def testPlotParams(self):
        self.gate.default_view().plot(self.ex, line_props = {'color' : 'grey'})

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

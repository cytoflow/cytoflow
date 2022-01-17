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
import cytoflow.utility as util
from .test_base import ImportedDataSmallTest


class TestDensityGate(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.gate = flow.DensityGateOp(name = "D",
                                       xchannel = "V2-A",
                                       ychannel = "Y2-A",
                                       xscale = "logicle",
                                       yscale = "logicle",
                                       keep = 0.8)

        
    def testEstimate(self):
        self.gate.estimate(self.ex)
        self.assertEqual(len(self.gate._keep_xbins[True]), 1635)
        self.assertEqual(len(self.gate._keep_ybins[True]), 1635)
    
    def testEstimateBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)

        self.assertEqual(len(self.gate._keep_xbins[1.0]), 1145)
        self.assertEqual(len(self.gate._keep_ybins[1.0]), 1145)
        self.assertEqual(len(self.gate._keep_xbins[10.0]), 1350)
        self.assertEqual(len(self.gate._keep_ybins[10.0]), 1350)
    
    def testApply(self):
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex) 
                 
        self.assertAlmostEqual(ex2.data.groupby("D").size().loc[True], 16218)
        self.assertAlmostEqual(ex2.data.groupby("D").size().loc[False], 3782)
            
        self.assertIsInstance(ex2.data.index, pd.RangeIndex)
        
    def testApplyBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        self.assertAlmostEqual(ex2.data.groupby(["Dox", "D"]).size().loc[1.0, False], 1866)
        self.assertAlmostEqual(ex2.data.groupby(["Dox", "D"]).size().loc[1.0, True], 8134)
        
        self.assertAlmostEqual(ex2.data.groupby(["Dox", "D"]).size().loc[10.0, False], 1859)
        self.assertAlmostEqual(ex2.data.groupby(["Dox", "D"]).size().loc[10.0, True], 8141)
 
    
    def testPlot(self):
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex)
        
    def testPlotUnusedFacet(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        with self.assertRaises(util.CytoflowViewError):
            self.gate.default_view().plot(self.ex)

    def testPlotBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex, plot_name = 1.0)        
        
    def testPlotProps(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex, contour_props = {'color' : 'b'})     

if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestDensityGate.testApplyBy']
    unittest.main()

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


class TestGaussian2D(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.gate = flow.GaussianMixtureOp(name = "Gauss",
                                           channels = ["V2-A", "Y2-A"],
                                           scale = {"V2-A" : "logicle",
                                                    "Y2-A" : "logicle"},
                                           num_components = 2,
                                           sigma = 1.0,
                                           posteriors = True)

        
    def testEstimate(self):
        self.gate.estimate(self.ex)
        self.assertAlmostEqual(self.gate._gmms[True].means_[0][0], 0.22138141, places = 3)
        self.assertAlmostEqual(self.gate._gmms[True].means_[0][1], 0.13820187, places = 3)
        self.assertAlmostEqual(self.gate._gmms[True].means_[1][0], 0.23076572, places = 3)
        self.assertAlmostEqual(self.gate._gmms[True].means_[1][1], 0.61884163, places = 3)
    
    def testEstimateBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)

        self.assertAlmostEqual(self.gate._gmms[(1.0,)].means_[0][0], 0.16641878, places = 3)
        self.assertAlmostEqual(self.gate._gmms[(1.0,)].means_[0][1], 0.14040044, places = 3)        
        self.assertAlmostEqual(self.gate._gmms[(1.0,)].means_[1][0], 0.35156931, places = 3)
        self.assertAlmostEqual(self.gate._gmms[(1.0,)].means_[1][1], 0.1459792, places = 3)
        self.assertAlmostEqual(self.gate._gmms[(10.0,)].means_[0][0], 0.16668259, places = 3)
        self.assertAlmostEqual(self.gate._gmms[(10.0,)].means_[0][1], 0.1328976, places = 3)        
        self.assertAlmostEqual(self.gate._gmms[(10.0,)].means_[1][0], 0.23071522, places = 3)
        self.assertAlmostEqual(self.gate._gmms[(10.0,)].means_[1][1], 0.61858629, places = 3)
    
    def testApply(self):
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex) 
                 
        self.assertLess(abs(ex2.data.groupby("Gauss", observed = True).size().loc["Gauss_1"] - 15565), 10)
        self.assertLess(abs(ex2.data.groupby("Gauss", observed = True).size().loc["Gauss_2"] - 4435), 10)

        self.assertLess(abs(ex2.data.groupby("Gauss_1", observed = True).size().loc[False] - 14793), 10)
        self.assertLess(abs(ex2.data.groupby("Gauss_1", observed = True).size().loc[True] - 5207), 10)
        
        self.assertLess(abs(ex2.data.groupby("Gauss_2", observed = True).size().loc[False] - 17992), 10)
        self.assertLess(abs(ex2.data.groupby("Gauss_2", observed = True).size().loc[True] - 2008), 10)
        
        self.assertIsInstance(ex2.data.index, pd.RangeIndex)
        
    def testApplyBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        self.assertLess(abs(ex2.data.groupby(["Gauss", "Dox"], observed = True).size().loc["Gauss_1", 1.0] - 5367), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss", "Dox"], observed = True).size().loc["Gauss_1", 10.0] - 5599), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss", "Dox"], observed = True).size().loc["Gauss_2", 1.0] - 4633), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss", "Dox"], observed = True).size().loc["Gauss_2", 10.0] - 4401), 10)
        
        self.assertLess(abs(ex2.data.groupby(["Gauss_1", "Dox"], observed = True).size().loc[False, 1.0] - 8128), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss_1", "Dox"], observed = True).size().loc[False, 10.0] - 8006), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss_1", "Dox"], observed = True).size().loc[True, 1.0] - 1872), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss_1", "Dox"], observed = True).size().loc[True, 10.0] - 1994), 10)
        
        self.assertLess(abs(ex2.data.groupby(["Gauss_2", "Dox"], observed = True).size().loc[False, 1.0] - 7815), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss_2", "Dox"], observed = True).size().loc[False, 10.0] - 7987), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss_2", "Dox"], observed = True).size().loc[True, 1.0] - 2185), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss_2", "Dox"], observed = True).size().loc[True, 10.0] - 2013), 10)

        
    def testStatistics(self): 
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        stat = ex2.statistics["Gauss"]
        
        self.assertIn("Component", stat.index.names)
        self.assertIn("Dox", stat.index.names)       
    
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

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestGaussian2D.testStatistics']
    unittest.main()

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
from test_base import ImportedDataSmallTest


class TestGaussian1D(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.gate = flow.GaussianMixtureOp(name = "Gauss",
                                           channels = ["Y2-A"],
                                           sigma = 0.5,
                                           num_components = 2,
                                           scale = {"Y2-A" : "logicle"},
                                           posteriors = True)
        
    def testEstimate(self):
        self.gate.estimate(self.ex)
        self.assertAlmostEqual(self.gate._gmms[True].means_[0][0], 0.138241432978, places = 3)
        self.assertAlmostEqual(self.gate._gmms[True].means_[1][0], 0.618966640805, places = 3)
    
    def testEstimateBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[0][0], 0.14084352777, places = 3)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[1][0], 0.440063665988, places = 1)        
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[0][0], 0.133235845266, places = 3)
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[1][0], 0.618998444886, places = 3) 
        
    def testApply(self):
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        self.assertLess(abs(ex2.data.groupby("Gauss").size().loc["Gauss_1"] - 15565), 10)
        self.assertLess(abs(ex2.data.groupby("Gauss").size().loc["Gauss_2"] - 4435), 10)
        
        self.assertLess(abs(ex2.data.groupby("Gauss_1").size().loc[False] - 14558), 10)
        self.assertLess(abs(ex2.data.groupby("Gauss_1").size().loc[True] - 5442), 10)
        
        self.assertLess(abs(ex2.data.groupby("Gauss_2").size().loc[False] - 17813), 10)
        self.assertLess(abs(ex2.data.groupby("Gauss_2").size().loc[True] - 2187), 10)
                
    def testApplyBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        #print(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_1"])
        self.assertLess(abs(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_1", 1.0] - 9950), 10)
        self.assertLess(abs(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_1", 10.0] - 5610), 10)

        self.assertLess(abs(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_2", 10.0] - 4390), 10)
        
        self.assertLess(abs(ex2.data.groupby(["Gauss_1", "Dox"]).size().loc[False, 1.0] - 6618), 10)        
        self.assertLess(abs(ex2.data.groupby(["Gauss_1", "Dox"]).size().loc[False, 10.0] - 7952), 10)      
        self.assertLess(abs(ex2.data.groupby(["Gauss_1", "Dox"]).size().loc[True, 1.0] - 3381), 10)        
        self.assertLess(abs(ex2.data.groupby(["Gauss_1", "Dox"]).size().loc[True, 10.0] - 2048), 10)     
        
        self.assertLess(abs(ex2.data.groupby(["Gauss_2", "Dox"]).size().loc[False, 1.0] - 9980), 10)        
        self.assertLess(abs(ex2.data.groupby(["Gauss_2", "Dox"]).size().loc[False, 10.0] - 7826), 10)      
        self.assertLess(abs(ex2.data.groupby(["Gauss_2", "Dox"]).size().loc[True, 1.0] - 20), 10)        
        self.assertLess(abs(ex2.data.groupby(["Gauss_2", "Dox"]).size().loc[True, 10.0] - 2174), 10) 
        
    def testStatistics(self): 
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        stat = ex2.statistics[("Gauss", "mean")]
        
        self.assertIn("Dox", stat.index.names)
        self.assertIn("Component", stat.index.names)
        self.assertIn("Channel", stat.index.names)
        
    def testPlot(self):
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex)
        
    def testPlotByException(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        with self.assertRaises(util.CytoflowViewError):
            self.gate.default_view().plot(self.ex)
        
    def testPlotBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex, plot_name = 1.0)
        

if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestGaussian1D.testApply']
    unittest.main()

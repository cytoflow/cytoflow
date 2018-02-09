#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

import matplotlib
matplotlib.use('Agg')

import cytoflow as flow
import cytoflow.utility as util

class Test(unittest.TestCase):

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"

        tube1 = flow.Tube(file = self.cwd + 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + 'CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        self.ex = import_op.apply()
        
        self.gate = flow.GaussianMixture1DOp(name = "Gauss",
                                             channel = "Y2-A",
                                             sigma = 0.5,
                                             num_components = 2,
                                             scale = "logicle",
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
        
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size().loc["Gauss_1"], 5442)
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size().loc["Gauss_2"], 2187)
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size().loc["Gauss_None"], 12371)
        
    def testApplyBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        #print(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_1"])
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_1", 1.0], 3382)
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_1", 10.0], 2048)

        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_2", 10.0], 2174)
        
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_None", 1.0], 6618)        
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_None", 10.0], 5778)      
        
    def testStatistics(self): 
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        stat = ex2.statistics[("Gauss", "mean")]
        
        self.assertIn("Gauss", stat.index.names)
        self.assertIn("Dox", stat.index.names)
        
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
#     import sys;sys.argv = ['', 'Test.testApply']
    unittest.main()
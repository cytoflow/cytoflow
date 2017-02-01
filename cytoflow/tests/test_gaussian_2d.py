#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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
import os

import matplotlib
matplotlib.use('Agg')

import cytoflow as flow

class Test(unittest.TestCase):

    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
        tube1 = flow.Tube(file = self.cwd + 'RFP_Well_A3.fcs', conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file= self.cwd + 'CFP_Well_A4.fcs', conditions = {"Dox" : 1.0})
        import_op = flow.ImportOp(conditions = {"Dox" : "float"},
                                  tubes = [tube1, tube2])
        self.ex = import_op.apply()

        self.gate = flow.GaussianMixture2DOp(name = "Gauss",
                                             xchannel = "V2-A",
                                             ychannel = "Y2-A",
                                             xscale = "logicle",
                                             yscale = "logicle",
                                             num_components = 2,
                                             sigma = 2.0,
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

        self.assertAlmostEqual(self.gate._gmms[1.0].means_[0][0], 0.16641878, places = 3)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[0][1], 0.14040044, places = 3)        
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[1][0], 0.35156931, places = 3)
        self.assertAlmostEqual(self.gate._gmms[1.0].means_[1][1], 0.1459792, places = 3)
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[0][0], 0.16668259, places = 3)
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[0][1], 0.1328976, places = 3)        
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[1][0], 0.23071522, places = 3)
        self.assertAlmostEqual(self.gate._gmms[10.0].means_[1][1], 0.61858629, places = 3)
    
    def testApply(self):
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex) 
                 
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size().loc["Gauss_1"], 5207)
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size().loc["Gauss_2"], 2008)
        self.assertAlmostEqual(ex2.data.groupby("Gauss").size().loc["Gauss_None"], 12785)
        
    def testApplyBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_1", 1], 1874)
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_1", 10], 1994)
        
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_2", 1], 2186)
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_2", 10], 2013)
         
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_None", 1], 5940)        
        self.assertAlmostEqual(ex2.data.groupby(["Gauss", "Dox"]).size().loc["Gauss_None", 10], 5993) 
        
    def testStatistics(self): 
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        ex2 = self.gate.apply(self.ex)
        
        stat = ex2.statistics[("Gauss", "xmean")]
        
        self.assertIn("Gauss", stat.index.names)
        self.assertIn("Dox", stat.index.names)       
    
    def testPlot(self):
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex)
        
    def testPlotBy(self):
        self.gate.by = ["Dox"]
        self.gate.estimate(self.ex)
        self.gate.default_view().plot(self.ex)
        

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
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

import os
import warnings
import unittest

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
        ex = import_op.apply()

        # this works so much better on transformed data
        logicle = flow.LogicleTransformOp()
        logicle.name = "Logicle transformation"
        logicle.channels = ['V2-A', 'Y2-A']
        logicle.estimate(ex)
        self.ex = logicle.apply(ex)
        
    def testBarChart(self):
        flow.BarChartView(name = "Bar Chart",
                          channel = "Y2-A",
                          variable = "Dox",
                          function = len).plot(self.ex)
                          
    def testHexBin(self):
        # suppress unicode warning.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            flow.HexbinView(name = "Hexbin",
                            xchannel = "V2-A",
                            ychannel = "Y2-A",
                            huefacet = "Dox").plot(self.ex)
                        
    def testHistogram(self):
        flow.HistogramView(name = "Histogram",
                           channel = "V2-A",
                           huefacet = "Dox").plot(self.ex)
                           
    def testScatterplot(self):
        flow.ScatterplotView(name = "Scatterplot",
                             xchannel = "V2-A",
                             ychannel = "Y2-A",
                             huefacet = "Dox").plot(self.ex)
                             
    def testStats1D(self):
        import numpy as np
        flow.Stats1DView(name = "Stats1D",
                         by = "Dox",
                         ychannel = "V2-A",
                         yfunction = np.mean).plot(self.ex)
                         
    def testStats2D(self):
        import numpy as np
        flow.Stats2DView(name = "Stats2D",
                         by = "Dox",
                         xchannel = "V2-A",
                         xfunction = np.mean,
                         ychannel = "Y2-A",
                         yfunction = np.mean).plot(self.ex)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        unittest.main()
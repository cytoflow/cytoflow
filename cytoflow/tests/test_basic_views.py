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
        self.ex = import_op.apply()
        
    def testBarChart(self):
        import numpy as np
        ex2 = flow.ChannelStatisticOp(name = "Stats1D",
                                      by = ["Dox"],
                                      channel = "V2-A",
                                      function = np.mean).apply(self.ex) 
                                      
        warnings.filterwarnings('ignore', 'axes.color_cycle is deprecated and replaced with axes.prop_cycle')

        flow.BarChartView(statistic = ("Stats1D", "mean"),
                          variable = "Dox").plot(ex2)
                    
    def testHexBin(self):
        # suppress unicode warning.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            flow.Histogram2DView(xchannel = "V2-A",
                                 ychannel = "Y2-A",
                                 huefacet = "Dox").plot(self.ex)
                           
    def testHistogram(self):
        flow.HistogramView(channel = "V2-A",
                           huefacet = "Dox").plot(self.ex)
                           
        flow.HistogramView(channel = "V2-A",
                           huefacet = "Dox",
                           scale = "log").plot(self.ex)
                           
        flow.HistogramView(channel = "V2-A",
                           huefacet = "Dox",
                           scale = "logicle").plot(self.ex)
                           
    def testScatterplot(self):
        flow.ScatterplotView(xchannel = "V2-A",
                             ychannel = "Y2-A",
                             huefacet = "Dox").plot(self.ex)
                             
        flow.ScatterplotView(xchannel = "V2-A",
                             ychannel = "Y2-A",
                             xscale = "log",
                             yscale = "log",
                             huefacet = "Dox").plot(self.ex)
                             
        flow.ScatterplotView(xchannel = "V2-A",
                             ychannel = "Y2-A",
                             xscale = "logicle",
                             yscale = "logicle",
                             huefacet = "Dox").plot(self.ex)
                             
    def testStats1D(self):
        import numpy as np
        
        ex2 = flow.ChannelStatisticOp(name = "Stats1D",
                                      by = ["Dox"],
                                      channel = "V2-A",
                                      function = np.mean).apply(self.ex)
        
        flow.Stats1DView(statistic = ("Stats1D", "mean"),
                         variable = "Dox").plot(ex2)
                         
        flow.Stats1DView(statistic = ("Stats1D", "mean"),
                         variable = "Dox",
                         xscale = "log",
                         yscale = "logicle").plot(ex2)

                         
    def testStats2D(self):
        import numpy as np
        
        ex2 = flow.ChannelStatisticOp(name = "StatsV",
                                      by = ["Dox"],
                                      channel = "V2-A",
                                      function = np.mean).apply(self.ex)
                                      
        ex3 = flow.ChannelStatisticOp(name = "StatsY",
                                      by = ["Dox"],
                                      channel = "Y2-A",
                                      function = np.mean).apply(ex2)                                      
        
        flow.Stats2DView(xstatistic = ("StatsV", "mean"),
                         ystatistic = ("StatsY", "mean"),
                         variable = "Dox").plot(ex3)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    with warnings.catch_warnings():
        warnings.filterwarnings('error')
        unittest.main()

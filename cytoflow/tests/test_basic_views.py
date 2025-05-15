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

import warnings
import unittest

import cytoflow as flow
from .test_base import ImportedDataSmallTest


class Test(ImportedDataSmallTest):

    def testBarChart(self):
        import numpy as np
        ex2 = flow.ChannelStatisticOp(name = "Stats1D",
                                      by = ["Dox"],
                                      channel = "V2-A",
                                      function = np.mean).apply(self.ex) 
                                      
        warnings.filterwarnings('ignore', 'axes.color_cycle is deprecated and replaced with axes.prop_cycle')

        flow.BarChartView(statistic = "Stats1D",
                          feature = "V2-A",
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
                             xscale = "linear",
                             yscale = "linear",
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

        # try setting default scale and _not_ setting xscale, yscale
        flow.set_default_scale("log")
        self.assertEqual(flow.get_default_scale(), "log")
        flow.ScatterplotView(xchannel = "V2-A",
                             ychannel = "Y2-A",
                             huefacet = "Dox").plot(self.ex)

        flow.set_default_scale("linear")  # reset the default scale
                             
    def testStats1D(self):
        import numpy as np
        
        ex2 = flow.ChannelStatisticOp(name = "Stats1D",
                                      by = ["Dox"],
                                      channel = "V2-A",
                                      function = np.mean).apply(self.ex)
        
        flow.Stats1DView(statistic = "Stats1D",
                         feature = "V2-A",
                         variable = "Dox").plot(ex2)
                         
        flow.Stats1DView(statistic = "Stats1D",
                         feature = "V2-A",
                         variable = "Dox",
                         variable_scale = "log",
                         scale = "logicle").plot(ex2)

                         
    def testStats2D(self):
        import pandas as pd
        op = flow.FrameStatisticOp(name = "ByDox",
                                   by = ['Dox'],
                                   function = lambda x: pd.Series({'Y2-A' : x['Y2-A'].mean(),
                                                                   'V2-A' : x['V2-A'].mean()}))
        ex = op.apply(self.ex)                                     
        
        flow.Stats2DView(statistic = "ByDox",
                         xfeature = "Y2-A",
                         yfeature = "V2-A",
                         variable = "Dox").plot(ex)


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testBarChart']
    unittest.main()

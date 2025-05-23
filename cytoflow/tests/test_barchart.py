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
import cytoflow.utility as util

from .test_base import ImportedDataTest  # @UnresolvedImport

class TestBarChart(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.ex = flow.ChannelStatisticOp(name = "ByDox",
                                     by = ['Dox', 'Well'],
                                     channel = "Y2-A",
                                     function = flow.geom_mean).apply(self.ex)
                                         
        self.view = flow.BarChartView(statistic = "ByDox",
                                      feature = "Y2-A",
                                      variable = "Well",
                                      huefacet = "Dox")
        
    def testPlot(self):
        self.view.plot(self.ex)
        
    def testXfacet(self):
        self.view.huefacet = ""
        self.view.xfacet = "Dox"
        self.view.plot(self.ex)
        
        
    def testYfacet(self):
        self.view.huefacet = ""
        self.view.yfacet = "Dox"
        self.view.plot(self.ex)

        
    def testScale(self):
        self.view.scale = "log"
        self.view.huescale = "log"
        self.view.plot(self.ex)
        
    def testSubset(self):
        self.view.huefacet = ""
        self.view.subset = "Dox == 10.0"
        with self.assertWarns(util.CytoflowViewWarning):
            self.view.plot(self.ex)

        
    def testSubset2(self):
        self.view.subset = "Well != 'A'"
        self.view.plot(self.ex)
        
    def testErrorStat(self):
        import pandas as pd
        
        self.ex = flow.ChannelStatisticOp(name = "ByDox2",
                                          by = ['Dox', 'Well'],
                                          channel = "Y2-A",
                                          function = lambda x: pd.Series({'Mean' : x.mean(), 
                                                                          'SD' : x.std(),
                                                                          'MeanLo' : x.mean() - x.mean() * 0.2,
                                                                          'MeanHi' : x.mean() + x.mean() * 0.2,
                                                                          'SDLo' : x.std() - x.std() * 0.2,
                                                                          'SDHi' : x.std() + x.std() * 0.2})).apply(self.ex)
        self.view.statistic = "ByDox2"
        self.view.feature = "Mean"
        self.view.error_low = "MeanLo"
        self.view.error_high = "MeanHi"
        self.view.plot(self.ex)
        
    # Base plot params
    
    def testTitle(self):
        self.view.plot(self.ex, title = "Title")
        
    def testXlabel(self):
        self.view.plot(self.ex, xlabel = "X lab")
        
    def testYlabel(self):
        self.view.plot(self.ex, ylabel = "Y lab")
        
    def testHueLabel(self):
        self.view.plot(self.ex, huelabel = "hue lab")
    
    def testColWrap(self):
        self.view.huefacet = ""
        self.view.xfacet = "Dox"
        self.view.plot(self.ex, col_wrap = 2)
        
    def testShareAxes(self):
        self.view.plot(self.ex, sharex = False, sharey = False)
        
    def testStyle(self):
        self.view.plot(self.ex, sns_style = "darkgrid")
        self.view.plot(self.ex, sns_style = "whitegrid")
        self.view.plot(self.ex, sns_style = "dark")
        self.view.plot(self.ex, sns_style = "white")
        self.view.plot(self.ex, sns_style = "ticks")
        
    def testContext(self):
        self.view.plot(self.ex, sns_context = "paper")
        self.view.plot(self.ex, sns_context = "notebook")
        self.view.plot(self.ex, sns_context = "talk")
        self.view.plot(self.ex, sns_context = "poster")

    def testDespine(self):
        self.view.plot(self.ex, despine = False)
        
    # 1D stats plot params
    def testOrientation(self):
        self.view.plot(self.ex, orientation = "horizontal")
        
    def testLim(self):
        self.view.plot(self.ex, lim = (0, 1000))
        
    # Bar chart bits
    
    def testErrWidth(self):
        self.view.plot(self.ex, errwidth = 5)
        
    def testErrColor(self):
        self.view.plot(self.ex, errcolor = "red")
    
    def testCapSize(self):
        self.view.plot(self.ex, capsize = 5)
         
    def testPlotParams(self):
        self.view.plot(self.ex,
                       title = "T",
                       xlabel = "X",
                       ylabel = "Y",
                       huelabel = "H",
                       sharex = False,
                       sharey = False,
                       lim = (0, 1),
                       sns_style = "dark",
                       sns_context = "paper",
                       despine = False,
                       orientation = "horizontal",
                       errwidth = 5,
                       errcolor = "red",
                       capsize = 3)
 



if __name__ == "__main__":
    # import sys;sys.argv = ['', 'TestBarChart.testErrorStat']
    unittest.main()

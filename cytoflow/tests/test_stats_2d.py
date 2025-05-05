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
import pandas as pd

import cytoflow as flow
import cytoflow.utility as util

from .test_base import ImportedDataTest

class Test2DStats(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)
                   
        self.ex = flow.ChannelStatisticOp(name = "ByDox",
                                          channel = "Y2-A",
                                          by = ['Well', 'Dox'],
                                          function = lambda x: pd.Series({'Mean' : x.mean(), 
                                                                          'SD' : x.std(),
                                                                          'MeanLo' : x.mean() - x.mean() * 0.2,
                                                                          'MeanHi' : x.mean() + x.mean() * 0.2,
                                                                          'SDLo' : x.std() - x.std() * 0.2,
                                                                          'SDHi' : x.std() + x.std() * 0.2})).apply(self.ex)
                                     
        self.view = flow.Stats2DView(statistic = "ByDox", 
                                     x_feature = "Mean",
                                     x_error_low = "MeanLo",
                                     x_error_high = "MeanHi",
                                     y_feature = "SD",
                                     y_error_low = "SDLo",
                                     y_error_high = "SDHi",
                                     variable = "Dox",
                                     huefacet = "Well")
        
    def testPlot(self):
        self.view.plot(self.ex)
        
    def testBadXErrorStatistic(self):
        self.view = flow.Stats2DView(statistic = "ByDox", 
                                     x_feature = "Mean",
                                     x_error_low = "MeanLo_BAD",
                                     x_error_high = "MeanHi",
                                     y_feature = "SD",
                                     y_error_low = "SDLo",
                                     y_error_high = "SDHi",
                                     variable = "Dox",
                                     huefacet = "Well")
        
        self.assertRaises(util.CytoflowViewError, self.view.plot, self.ex)

        
    def testBadYErrorStatistic(self):
        self.view = flow.Stats2DView(statistic = "ByDox", 
                                     x_feature = "Mean",
                                     x_error_low = "MeanLo_BAD",
                                     x_error_high = "MeanHi",
                                     y_feature = "SD",
                                     y_error_low = "SDLo",
                                     y_error_high = "SDHi_BAD",
                                     variable = "Dox",
                                     huefacet = "Well")
        
        self.assertRaises(util.CytoflowViewError, self.view.plot, self.ex)

        
    def testXfacet(self):
        self.view.huefacet = ""
        self.view.xfacet = "Well"
        self.view.plot(self.ex)
        
        
    def testYfacet(self):
        self.view.huefacet = ""
        self.view.yfacet = "Well"
        self.view.plot(self.ex)

    def testLog(self):
        self.view.xscale = "log"
        self.view.yscale = "log"
        self.view.plot(self.ex)
        
    def testLogicle(self):
        self.view.xscale = "logicle"
        self.view.yscale = "logicle"
        self.view.plot(self.ex)
        
    def testSubset(self):
        self.view.huefacet = ""
        self.view.subset = "Well == 'A'"
        with self.assertWarns(util.CytoflowViewWarning):
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
        self.view.xfacet = "Well"
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
        
    # 2D stats plot params
        
    def testXLim(self):
        self.view.plot(self.ex, xlim = (0, 1000))

    def testYLim(self):
        self.view.plot(self.ex, ylim = (0, 1000))
        
    # 2D stats bits
        
    def testLineStyle(self):
        self.view.plot(self.ex, linestyle = 'solid')
        self.view.plot(self.ex, linestyle = 'dashed')
        self.view.plot(self.ex, linestyle = 'dashdot')
        self.view.plot(self.ex, linestyle = 'dotted')
        self.view.plot(self.ex, linestyle = 'none')

    def testLineWidth(self):
        self.view.plot(self.ex, linestyle = 'solid', linewidth = 5)
        
    def testMarker(self):
        for mk in ["o", ",", "v", "^", "<", ">", "1", "2", "3", "4", "8",
                       "s", "p", "*", "h", "H", "+", "x", "D", "d", ""]:
            self.view.plot(self.ex, marker = mk)
            
    def testMarkerSize(self):
        self.view.plot(self.ex, markersize = 10)

    def testCapSize(self):
        self.view.plot(self.ex, capsize = 10)
        
    def testAlpha(self):
        self.view.plot(self.ex, alpha = 0.33)
        

if __name__ == "__main__":
    import sys;sys.argv = ['', 'Test2DStats.testBadYErrorStatistic']
    unittest.main()

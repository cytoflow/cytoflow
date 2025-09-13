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

import unittest
import pandas as pd

import cytoflow as flow
import cytoflow.utility as util

from .test_base import ImportedDataTest

class TestMatrix(ImportedDataTest):

    def setUp(self):
        super().setUp()

        self.ex = flow.ThresholdOp(name = "Threshold",
                                   channel = "Y2-A",
                                   threshold = 500).apply(self.ex)
                   
        self.ex = flow.ChannelStatisticOp(name = "ByDox",
                                          channel = "Y2-A",
                                          by = ['Well', 'Dox'],
                                          function = lambda x: pd.Series({'Mean' : x.mean(), 
                                                                          'SD' : x.std(),
                                                                          'MeanLo' : x.mean() - x.mean() * 0.2,
                                                                          'MeanHi' : x.mean() + x.mean() * 0.2,
                                                                          'SDLo' : x.std() - x.std() * 0.2,
                                                                          'SDHi' : x.std() + x.std() * 0.2})).apply(self.ex)
                                                                          
        self.ex = flow.ChannelStatisticOp(name = "ByDoxRev",
                                          channel = "Y2-A",
                                          by = ['Dox', 'Well'],
                                          function = lambda x: pd.Series({'Mean' : x.mean(), 
                                                                          'SD' : x.std(),
                                                                          'MeanLo' : x.mean() - x.mean() * 0.2,
                                                                          'MeanHi' : x.mean() + x.mean() * 0.2,
                                                                          'SDLo' : x.std() - x.std() * 0.2,
                                                                          'SDHi' : x.std() + x.std() * 0.2})).apply(self.ex)
                                                                          
        self.ex = flow.ChannelStatisticOp(name = "ByDoxThreshold",
                                          channel = "Y2-A",
                                          by = ['Well', 'Dox', 'Threshold'],
                                          function = lambda x: pd.Series({'Len' : len(x),
                                                                          'Mean' : x.mean(), 
                                                                          'SD' : x.std(),
                                                                          'MeanLo' : x.mean() - x.mean() * 0.2,
                                                                          'MeanHi' : x.mean() + x.mean() * 0.2,
                                                                          'SDLo' : x.std() - x.std() * 0.2,
                                                                          'SDHi' : x.std() + x.std() * 0.2})).apply(self.ex)
                                     
        self.view = flow.MatrixView(statistic = "ByDox", 
                                    feature = "Mean",
                                    xfacet = "Dox",
                                    yfacet = "Well",
                                    style = "heat")
        
    def testHeat(self):
        self.view.style = "heat"
        self.view.plot(self.ex)
        
    def testHeatRev(self):
        self.view.style = "heat"
        self.view.statistic = "ByDoxRev"
        self.view.plot(self.ex)
        
    def testHeatJustX(self):
        self.view.yfacet = ""
        self.view.plot(self.ex, plot_name = "C")
        
    def testHeatJustY(self):
        self.view.xfacet = ""
        self.view.plot(self.ex, plot_name = 0.0)
        
    def testPie(self):
        self.view.style = "pie"
        self.view.statistic = "ByDoxThreshold"
        self.view.variable = "Threshold"
        self.view.feature = "Len"
        self.view.plot(self.ex)
        
    def testPieJustX(self):
        self.view.style = "pie"
        self.view.statistic = "ByDoxThreshold"
        self.view.variable = "Threshold"
        self.view.feature = "Len"
        self.view.yfacet = ""
        self.view.plot(self.ex, plot_name = "C")
        
    def testPieJustY(self):
        self.view.style = "pie"
        self.view.statistic = "ByDoxThreshold"
        self.view.variable = "Threshold"
        self.view.feature = "Len"
        self.view.xfacet = ""
        self.view.plot(self.ex, plot_name = 0.0)
        
    def testPieRev(self):
        self.view.statistic = "ByDoxRev"
        self.view.style = "pie"
        self.view.xfacet = ""
        self.view.variable = "Dox"
        self.view.plot(self.ex)
        
    def testPetal(self):
        self.view.style = "petal"
        self.view.statistic = "ByDoxThreshold"
        self.view.variable = "Threshold"
        self.view.feature = "Len"
        self.view.plot(self.ex)
        
    def testPetalJustX(self):
        self.view.style = "petal"
        self.view.statistic = "ByDoxThreshold"
        self.view.variable = "Threshold"
        self.view.feature = "Len"
        self.view.yfacet = ""
        self.view.plot(self.ex, plot_name = "C")
        
    def testPetalJustY(self):
        self.view.style = "petal"
        self.view.statistic = "ByDoxThreshold"
        self.view.variable = "Threshold"
        self.view.feature = "Len"
        self.view.xfacet = ""
        self.view.plot(self.ex, plot_name = 0.0)
        
    def testPetalRev(self):
        self.view.statistic = "ByDoxRev"
        self.view.style = "petal"
        self.view.xfacet = ""
        self.view.variable = "Dox"
        self.view.plot(self.ex)
        


    def testLog(self):
        self.view.scale = "log"
        self.view.plot(self.ex)
        
    def testLogicle(self):
        self.view.scale = "logicle"
        self.view.plot(self.ex)
        
    def testSubset(self):
        self.view.subset = "Well == 'A'"
        self.view.yfacet = ""
        with self.assertWarns(util.CytoflowViewWarning):
            self.view.plot(self.ex)
            
    def testBothIndexAndColumnEnum(self):
        self.view.statistic = "Conditions"
        self.view.feature = "Dox"
        self.view.enum_plots(self.ex)
        
    def testBothIndexAndColumn(self):
        self.view.statistic = "Conditions"
        self.view.feature = "Dox"
        self.view.plot(self.ex)
        
    # Base plot params
    
    def testTitle(self):
        self.view.plot(self.ex, title = "Title")
        
    def testXlabel(self):
        self.view.plot(self.ex, xlabel = "X lab")
        
    def testYlabel(self):
        self.view.plot(self.ex, ylabel = "Y lab")
        
    def testLegendLabel(self):
        self.view.plot(self.ex, legendlabel = "hue lab")
        

if __name__ == "__main__":
    import sys;sys.argv = ['', 'Test2DStats.testBadYErrorStatistic']
    unittest.main()

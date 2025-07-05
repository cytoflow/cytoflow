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
                   
        self.ex = flow.ChannelStatisticOp(name = "ByDox",
                                          channel = "Y2-A",
                                          by = ['Well', 'Dox'],
                                          function = lambda x: pd.Series({'Mean' : x.mean(), 
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
        
    def testPie(self):
        self.view.style = "pie"
        self.view.xfacet = ""
        self.view.variable = "Dox"
        self.view.plot(self.ex)
        
    def testPetal(self):
        self.view.style = "petal"
        self.view.xfacet = ""
        self.view.variable = "Dox"
        self.view.plot(self.ex)
        
    def testJustXfacet(self):
        self.view.yfacet = ""
        self.view.plot(self.ex, plot_name = "C")
        
    def testJustYfacet(self):
        self.view.xfacet = ""
        self.view.plot(self.ex, plot_name = 0.0)

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

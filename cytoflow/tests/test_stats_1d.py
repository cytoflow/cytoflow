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

import unittest

import cytoflow as flow
import cytoflow.utility as util

from test_base import ImportedDataTest  # @UnresolvedImport

class Test1DStats(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)
        self.ex = flow.ThresholdOp(name = "T",
                                   channel = "Y2-A",
                                   threshold = 500).apply(self.ex)
                                   
        self.ex = flow.ChannelStatisticOp(name = "ByDox",
                             channel = "Y2-A",
                             by = ['T', 'Dox'],
                             function = flow.geom_mean).apply(self.ex)
                             
        self.ex = flow.ChannelStatisticOp(name = "ByDox",
                             channel = "Y2-A",
                             by = ['T', 'Dox'],
                             function = flow.geom_sd_range).apply(self.ex)
                                     
        self.view = flow.Stats1DView(statistic = ("ByDox", "geom_mean"),
                                     error_statistic = ("ByDox", "geom_sd_range"),
                                     variable = "Dox",
                                     huefacet = "T")
        
    def testPlot(self):
        self.view.plot(self.ex)
        
    def testBadErrorStat(self):
        self.ex = flow.ChannelStatisticOp(name = "ByDox_BAD",
                                          channel = "Y2-A",
                                          by = ['Dox'],
                                          function = flow.geom_sd_range).apply(self.ex)
                                     
        self.view = flow.Stats1DView(statistic = ("ByDox", "geom_mean"),
                                     error_statistic = ("ByDox_BAD", "geom_sd_range"),
                                     variable = "Dox",
                                     huefacet = "T")
        
        self.assertRaises(util.CytoflowViewError, self.view.plot, self.ex)
        
    def testXfacet(self):
        self.view.huefacet = ""
        self.view.xfacet = "T"
        self.view.plot(self.ex)
        
        
    def testYfacet(self):
        self.view.huefacet = ""
        self.view.yfacet = "T"
        self.view.plot(self.ex)

        
    def testScale(self):
        self.view.scale = "log"
        self.view.huescale = "log"
        self.view.plot(self.ex)
        
    def testSubset(self):
        self.view.huefacet = ""
        self.view.subset = "T == True"
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
        self.view.variable = "Dox"
        self.view.huefacet = ""
        self.view.xfacet = "T"
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
        
    # 1D stats bits
    
    def testVariableLim(self):
        self.view.plot(self.ex, variable_lim = (2, 5))
        
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
        
    def testShadeX(self):
        self.view.plot(self.ex, shade_error = True, orientation = 'horizontal')
        
    def testShadeY(self):
        self.view.plot(self.ex, shade_error = True)
        

if __name__ == "__main__":
    import sys;sys.argv = ['', 'Test1DStats.testBadErrorStat']
    unittest.main()
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
Created on Mar 5, 2018

@author: brian
'''

import unittest

import matplotlib
matplotlib.use('Agg')

import cytoflow as flow
from cytoflow.tests.test_base import ImportedDataTest

class TestKde2D(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)
        self.view = flow.Kde2DView(xchannel = "B1-A",
                                   ychannel = "Y2-A")
        
    def testPlot(self):
        self.view.plot(self.ex)
        
    def testLogScale(self):
        self.view.xscale = "log"
        self.view.yscale = "log"
        self.view.plot(self.ex)
        
    def testLogicleScale(self):
        self.view.xscale = "logicle"
        self.view.yscale = "logicle"
        self.view.plot(self.ex)
        
    def testXFacet(self):
        self.view.xfacet = "Dox"
        self.view.plot(self.ex)
        
    def testYFacet(self):
        self.view.yfacet = "Dox"
        self.view.plot(self.ex)

    def testHueFacet(self):
        self.view.huefacet = "Dox"
        self.view.plot(self.ex)
        
    def testSubset(self):
        self.view.subset = "Dox == 10.0"
        self.view.plot(self.ex)
        
    # Base plot params
    
    def testTitle(self):
        self.view.plot(self.ex, title = "Title")
        
    def testXlabel(self):
        self.view.plot(self.ex, xlabel = "X lab")
        
    def testYlabel(self):
        self.view.plot(self.ex, ylabel = "Y lab")

    def testHuelabel(self):
        self.view.huefacet = "Dox"
        self.view.plot(self.ex, huelabel = "Y lab")
    
    def testColWrap(self):
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

    # Data plot params
    
    def testQuantiles(self):
        self.view.plot(self.ex, min_quantile = 0.01, max_quantile = 0.90)
        
    # 2D data plot params
    def testLimits(self):
        self.view.plot(self.ex, xlim = (0, 1000), ylim = (0, 1000))

    # Kde 2d params
    def testShade(self):
        self.view.plot(self.ex, shade = False)
        
    def testAlpha(self):
        self.view.plot(self.ex, min_alpha = 0.5, max_alpha = 0.7) 
        
    def testLevels(self):
        self.view.plot(self.ex, n_levels = 5)
        
    def testLineStyle(self):
        self.view.plot(self.ex, linestyle = 'solid')
        self.view.plot(self.ex, linestyle = 'dashed')
        self.view.plot(self.ex, linestyle = 'dashdot')
        self.view.plot(self.ex, linestyle = 'dotted')
        self.view.plot(self.ex, linestyle = 'none')

    def testLineWidth(self):
        self.view.plot(self.ex, linestyle = 'solid', linewidth = 5)
        
    def testGridsize(self):
        self.view.plot(self.ex, gridsize = 50)
        
    def testKernel(self):
        for k in ['gau', 'biw', 'cos', 'epa', 'tri', 'triw', 'uni']:
            self.view.plot(self.ex, kernel = k)
            
    def testBandwidth(self):
        for bw in ['scott', 'silverman']:
            self.view.plot(self.ex, bw = bw)
        
        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestKde2D.testBandwidth']
    unittest.main()
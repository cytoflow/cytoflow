#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
import cytoflow as flow
import matplotlib.pyplot as plt
import numpy as np

from test_base import View1DTestBase, get_legend_entries  # @UnresolvedImport


class TestViolin(View1DTestBase, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.view = flow.ViolinPlotView(channel = "B1-A",
                                        variable = "Dox")

    def testPlot(self):
        self.view.plot(self.ex)
        # plt.gcf().savefig("test.png")
        ax = plt.gca()
        assert ax.get_ylabel() == "B1-A"
        assert ax.get_xlabel() == "Dox"
        np.testing.assert_array_equal(
            ax.get_yticks(),
            np.array([-25000., 0, 25000., 50000., 75000., 100000., 125000.,
                      150000., 175000., 200000.])
            # NOTE -25000 not seen on the plot
        )
        assert [l.get_text() for l in ax.get_xticklabels()] == ["0.0", "10.0", "100.0"]

    def testSubset(self):
        self.view.subset = "Dox == 10.0"
        self.view.plot(self.ex)
        assert ['10.0'] == get_legend_entries(plt.gca())

    def testXFacet(self):
        self.view.xfacet = "Well"
        self.view.plot(self.ex)
        axs = plt.gcf().get_axes()
        assert ["Well = Aa", "Well = Bb", "Well = Cc"] == [ax.get_title() for ax in axs]
        
    def testYFacet(self):
        self.view.yfacet = "Well"
        self.view.plot(self.ex)
        axs = plt.gcf().get_axes()
        assert ["Well = Aa", "Well = Bb", "Well = Cc"] == [ax.get_title() for ax in axs]

    def testHueFacet(self):
        self.view.huefacet = "Well"
        self.view.plot(self.ex)
        assert ["Aa", "Bb", "Cc"] == get_legend_entries(plt.gca())

    def testSubset(self):
        self.view.subset = "Dox == 10.0"
        self.view.plot(self.ex)
        assert [l.get_text() for l in plt.gca().get_xticklabels()] == ["10.0"]
        
    def testHueLabel(self):
        # TODO this is different
        self.view.huefacet = "Well"
        self.view.plot(self.ex, huelabel = "hue lab")
    
    def testColWrap(self):
        # TODO this is different
        self.view.variable = "Well"
        self.view.xfacet = "Dox"
        self.view.plot(self.ex, col_wrap = 2)

    # Violin params
        
    def testBw(self):
        self.view.plot(self.ex, bw = 'scott')
        self.view.plot(self.ex, bw = 'silverman')
        
    def testScalePlot(self):
        self.view.plot(self.ex, scale_plot = 'area')
        self.view.plot(self.ex, scale_plot = 'count')
        self.view.plot(self.ex, scale_plot = 'width')
        
    def testGridsize(self):
        self.view.plot(self.ex, gridsize = 200)
        
    def testInner(self):
        self.view.plot(self.ex, inner = 'box')
        self.view.plot(self.ex, inner = 'quartile')
        self.view.plot(self.ex, inner = None)
        
    def testSplit(self):
        self.view.huefacet = 'Well'
        self.view.subset = 'Well != "Cc"'
        self.view.plot(self.ex, split = True)

        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestViolin.testPlot']
    unittest.main()

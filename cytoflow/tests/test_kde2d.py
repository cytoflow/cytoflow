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

from test_base import View2DTestBase  # @UnresolvedImport


class TestKde2D(View2DTestBase, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.view = flow.Kde2DView(xchannel = "B1-A",
                                   ychannel = "Y2-A")

    def testPlot(self):
        super().testPlot(
            true_x=(-25000., 0., 25000., 50000., 75000., 100000., 125000.,
                    150000., 175000., 200000.),
        )

    # Kde 2d params
    def testShade(self):
        self.view.plot(self.ex, shade = True)
        
    def testAlpha(self):
        self.view.plot(self.ex, min_alpha = 0.5, max_alpha = 0.7) 
        
    def testLevels(self):
        self.view.plot(self.ex, n_levels = 5)
        
    def testLineStyle(self):
        self.view.plot(self.ex, linestyles = 'solid')
        self.view.plot(self.ex, linestyles = 'dashed')
        self.view.plot(self.ex, linestyles = 'dashdot')
        self.view.plot(self.ex, linestyles = 'dotted')

    def testLineWidth(self):
        self.view.plot(self.ex, linestyles = 'solid', linewidths = 5)
        
    def testGridsize(self):
        self.view.plot(self.ex, gridsize = 50)

    def testBandwidth(self):
        for bw in ['scott', 'silverman', 0.1]:
            self.view.plot(self.ex, bw = bw)
            plt.close('all')
        
        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestKde2D.testKernel']
    unittest.main()

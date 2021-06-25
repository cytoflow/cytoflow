#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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

from .test_base import View2DTestBase

class TestDensityPlot(View2DTestBase, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.view = flow.DensityView(xchannel = "B1-A",
                                     ychannel = "Y2-A")

    def testPlot(self):
        super().testPlot(
            true_x=(-50000., 0., 50000., 100000., 150000., 200000.),
        )

    def testXFacet(self):
        super().testXFacet(has_colorbar=True)

    def testYFacet(self):
        super().testYFacet(has_colorbar=True)

    def testSubset(self):
        super().testSubset(has_colorbar=True)

    def testXFacetOrder(self):
        super().testXFacetOrder(has_colorbar=True)

    def testYFacetOrder(self):
        super().testYFacetOrder(has_colorbar=True)

    def testHueFacet(self):
        pass  # not applicable

    def testHueLabel(self):
        pass  # not applicable

    def testHueFacetOrder(self):
        pass  # not applicable

    # Density params
        
    def testGridsize(self):
        self.view.plot(self.ex, gridsize = 30)
        
    def testSmoothed(self):
        self.view.plot(self.ex, smoothed = True) 
        
    def testSmoothedSigma(self):
        self.view.plot(self.ex, smoothed = True, smoothed_sigma = 2) 
        
        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

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

from test_base import View1DTestBase  # @UnresolvedImport


class TestKde1D(View1DTestBase, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.view = flow.Kde1DView(channel = "B1-A")

    # KDE params
        
    def testShade(self):
        self.view.plot(self.ex, shade = False)
        
    def testAlpha(self):
        self.view.plot(self.ex, alpha = 0.5) 
        
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
        for k in ['gaussian','tophat','epanechnikov','exponential','linear','cosine']:
            self.view.plot(self.ex, kernel = k)
            
    def testBandwidth(self):
        for bw in ['scott', 'silverman', 1.0, 0.1, 0.01]:
            self.view.plot(self.ex, bw = bw)

        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

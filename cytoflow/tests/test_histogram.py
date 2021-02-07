#!/usr/bin/env python3.4
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

from test_base import View1DTestBase  # @UnresolvedImport

class TestHistogram(View1DTestBase, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.view = flow.HistogramView(channel = "B1-A")

    # Histogram params
        
    def testNumBins(self):
        self.view.plot(self.ex, num_bins = 20)
        
    def testStep(self):
        self.view.plot(self.ex, histtype = 'step') 
        
    def testBar(self):
        self.view.plot(self.ex, histtype = 'bar')
        
    def testLineStyle(self):
        self.view.plot(self.ex, histtype = 'step', linestyle = 'solid')
        self.view.plot(self.ex, histtype = 'step', linestyle = 'dashed')
        self.view.plot(self.ex, histtype = 'step', linestyle = 'dashdot')
        self.view.plot(self.ex, histtype = 'step', linestyle = 'dotted')
        
    def testLineWidth(self):
        self.view.plot(self.ex, histtype = 'step', linestyle = 'solid', linewidth = 5)
        
    def testNormed(self):
        self.view.huefacet = "Dox"
        self.view.plot(self.ex, histtype = 'step', density = True)

        
if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestHistogram.testLogicleScale']
    unittest.main()

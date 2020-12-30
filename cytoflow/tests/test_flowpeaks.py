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
Created on Dec 1, 2015

@author: brian
'''
import unittest
import os
import cytoflow as flow
from test_base import ImportedDataSmallTest


class TestFlowpeaks(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.op = flow.FlowPeaksOp(name = "FP",
                                   channels = ["V2-A", "Y2-A"],
                                   scale = {"V2-A" : "logicle",
                                            "Y2-A" : "logicle"},
                                   h0 = 0.5)

        
    def testEstimate(self):
        self.op.estimate(self.ex)
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['FP'].unique()), 2)
    
    def testEstimateBy(self):
        self.op.by = ["Dox"]
        self.op.estimate(self.ex)
        
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['FP'].unique()), 2)

    def testPlot(self):
        self.op.estimate(self.ex)
        self.op.default_view().plot(self.ex)

    def testPlotDensity(self):
        self.op.estimate(self.ex)
        self.op.default_view(density = True).plot(self.ex)

if __name__ == "__main__":
    import sys;sys.argv = ['', 'TestFlowpeaks.testPlotDensity']
    unittest.main()

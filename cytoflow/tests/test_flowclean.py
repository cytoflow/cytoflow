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

'''
Created on Dec 1, 2015

@author: brian
'''
import unittest
import cytoflow as flow
import pandas as pd
import os
from .test_base import ImportedDataSmallTest


class TestFlowClean(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.op = flow.FlowCleanOp(name = "FC",
                                   time_channel = "HDR-T",
                                   channels = ["V2-A", "Y2-A"],
                                   scale = {"V2-A" : "logicle",
                                            "Y2-A" : "logicle"})

        
    def testEstimate(self):
        self.op.estimate(self.ex)
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['FC'].unique()), 2)
        
        self.assertIsInstance(ex2.data.index, pd.RangeIndex)

    def testPlot(self):
        filename = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/RFP_Well_A3.fcs"
        self.op.estimate(self.ex)
        self.op.default_view().plot(self.ex, plot_name = filename)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestFlowpeaks.testPlotDensity']
    unittest.main()

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
Created on Nov 15, 2015

@author: brian
'''

import unittest
import cytoflow as flow
from test_base import ClosePlotsWhenDoneTest


class TestBeads(ClosePlotsWhenDoneTest):

    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/rby.fcs',
                                                   conditions = {})]).apply()        
        
        self.op = flow.BeadCalibrationOp(
                    units = {"PE-Tx-Red-YG-A" : "MEPTR"},
                    beads_file = self.cwd + '/data/tasbe/beads.fcs',
                    beads = flow.BeadCalibrationOp.BEADS["Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R"])
        self.op.estimate(self.ex)

    def testCalibrationFn(self):
        # the four "correct" values were determined using the Spherotech
        # linearization and QC spreadsheet from
        # http://www.spherotech.com/RCP-30-5a%20%20rev%20G.2.xls
        
        # 1. the beads file was plotted and the five brightest peaks' locations
        #    were determined manually
        
        # 2. IN THE MEPTR SHEET (which matches the PE-Tx-Red channel), the 
        #    peaks were converted to 256-relative-channel measurements using
        #    Table 4
        
        # 3. The 256 RCN measurements were copied to the normalization table.
        #    The MEPTR values were copied from the standard table (on the left.)
        
        # 4. The test values (100, 1000, 10000, 100000) were converted to
        #    256 RCN, and the converted values copied into the cross-calibration
        #    table.
         
        self.assertAlmostEqual(self.op._calibration_functions["PE-Tx-Red-YG-A"](100),
                               887.5296, delta = 0.1)
        
        self.assertAlmostEqual(self.op._calibration_functions["PE-Tx-Red-YG-A"](1000),
                               8911.2549, delta = 1)
                               
        self.assertAlmostEqual(self.op._calibration_functions["PE-Tx-Red-YG-A"](10000),
                               89473.5903, delta = 10)
                               
        self.assertAlmostEqual(self.op._calibration_functions["PE-Tx-Red-YG-A"](100000),
                               898360.9384, delta = 100)
        
    def testApply(self):
        # this is just to make sure the code doesn't crash;
        # nothing about correctness.
        
        ex2 = self.op.apply(self.ex)
        
        with self.assertRaises(ValueError):
            self.assertFalse((self.ex.data == ex2.data).all().all())

    def testPlot(self):
        # this is to make sure the code doesn't crash;
        # nothing about correctness
        
        self.op.default_view().plot(self.ex)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

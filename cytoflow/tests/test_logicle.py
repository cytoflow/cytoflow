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

import unittest

import pandas as pd

import cytoflow as flow
import cytoflow.utility as util

class TestLogicle(unittest.TestCase):
    
    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
        tube1 = flow.Tube(file = self.cwd + 'RFP_Well_A3.fcs', conditions = {})
        import_op = flow.ImportOp(conditions = {},
                                  tubes = [tube1])
        self.ex = import_op.apply()

        
    def test_logicle_estimate(self):
        """
        Test the parameter estimator against the R implementation
        """
        
        scale = util.scale_factory("logicle", self.ex, channel = "Y2-A")

        # these are the values the R implementation gives
        self.assertAlmostEqual(scale.A, 0.0)
        self.assertAlmostEqual(scale.W, 0.533191950161284)
        
    ### TODO - test the estimator failure modes
        
    def test_logicle_apply(self):
        """
        Make sure the function applies without segfaulting
        """
        
        scale = util.scale_factory("logicle", self.ex, channel = "Y2-A")
        
        x = scale(20.0)
        self.assertTrue(isinstance(x, float))
        
        x = scale([20])
        self.assertTrue(isinstance(x, list))
        
        x = scale(pd.Series([20]))
        self.assertTrue(isinstance(x, pd.Series))
        
    ### TODO - test the apply function error checking
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
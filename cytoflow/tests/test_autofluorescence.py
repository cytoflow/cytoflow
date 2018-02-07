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
Created on Oct 30, 2015

@author: brian
'''
import unittest

import matplotlib
matplotlib.use('Agg')

import cytoflow as flow

class TestExperiment(unittest.TestCase):
    """
    Unit tests for Experiment
    """

    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/blank.fcs',
                                                   conditions = {})]).apply()

        self.op = flow.AutofluorescenceOp(
                    blank_file = self.cwd + '/data/tasbe/blank.fcs',
                    channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"])
        self.op.estimate(self.ex)

    def test_estimate(self):
        self.assertAlmostEqual(self.op._af_median["FITC-A"], 3.480000019073486)
        self.assertAlmostEqual(self.op._af_median["Pacific Blue-A"], 12.800000190734863)
        self.assertAlmostEqual(self.op._af_median["PE-Tx-Red-YG-A"], 21.15999984741211)
        
        # I don't know why this gives different results on my machine 
        # and on Travis-CI.  Weeeeird.
        self.assertAlmostEqual(self.op._af_stdev["FITC-A"], 19.595919089919036, places = 2)
        self.assertAlmostEqual(self.op._af_stdev["Pacific Blue-A"], 20.28523486529143, places = 2)
        self.assertAlmostEqual(self.op._af_stdev["PE-Tx-Red-YG-A"], 51.66055254193842, places = 2)
                
    def test_apply(self):
        ex2 = self.op.apply(self.ex)
        
        import numpy as np
        self.assertAlmostEqual(np.median(ex2["FITC-A"]), 0.0)
        self.assertAlmostEqual(np.median(ex2["Pacific Blue-A"]), 0.0)
        self.assertAlmostEqual(np.median(ex2["PE-Tx-Red-YG-A"]), 0.0)
        
        with self.assertRaises(ValueError):
            self.assertFalse((self.ex.data == ex2.data).all().all())
        
    def test_plot(self):
        self.op.default_view().plot(self.ex)
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
        
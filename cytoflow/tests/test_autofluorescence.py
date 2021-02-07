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
Created on Oct 30, 2015

@author: brian
'''
import unittest
import cytoflow as flow
from test_base import ClosePlotsWhenDoneTest


class TestAutofluorescence(ClosePlotsWhenDoneTest):
    """
    Unit tests for Autofluorescence
    """

    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {'Dox' : 'int'},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/eyfp.fcs',
                                                   conditions = {'Dox' : 1.0}),
                                         flow.Tube(file = self.cwd + '/data/tasbe/mkate.fcs',
                                                   conditions = {'Dox' : 10.0})]).apply()

        self.op = flow.AutofluorescenceOp(
                    blank_file = self.cwd + '/data/tasbe/blank.fcs',
                    channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"])
        self.op.estimate(self.ex)

    def testEstimate(self):
        self.assertAlmostEqual(self.op._af_median["FITC-A"], 3.480000019073486)
        self.assertAlmostEqual(self.op._af_median["Pacific Blue-A"], 12.800000190734863)
        self.assertAlmostEqual(self.op._af_median["PE-Tx-Red-YG-A"], 21.15999984741211)
        
        # I don't know why this gives different results on my machine 
        # and on Travis-CI.  Weeeeird.
        self.assertAlmostEqual(self.op._af_stdev["FITC-A"], 19.595919089919036, places = 2)
        self.assertAlmostEqual(self.op._af_stdev["Pacific Blue-A"], 20.28523486529143, places = 2)
        self.assertAlmostEqual(self.op._af_stdev["PE-Tx-Red-YG-A"], 51.66055254193842, places = 2)
                
    def testApply(self):
        
        ex = flow.ImportOp(tubes = [flow.Tube(file = self.cwd + '/data/tasbe/blank.fcs')]).apply()
        ex2 = self.op.apply(ex)
        
        import numpy as np
        self.assertAlmostEqual(np.median(ex2["FITC-A"]), 0.0)
        self.assertAlmostEqual(np.median(ex2["Pacific Blue-A"]), 0.0)
        self.assertAlmostEqual(np.median(ex2["PE-Tx-Red-YG-A"]), 0.0)
        
        with self.assertRaises(ValueError):
            self.assertFalse((self.ex.data == ex2.data).all().all())
        
    def testPlot(self):
        self.op.default_view().plot(self.ex)
        
    def testConditions(self):
        
        gm_1 = flow.GaussianMixtureOp(name = "Morpho1",
                                      channels = ["FSC-A", "SSC-A"],
                                      scale = {"SSC-A" : "log"},
                                      num_components = 2,
                                      sigma = 2,
                                      by = ['Dox'])
        gm_1.estimate(self.ex)
        ex_morpho = gm_1.apply(self.ex)
        
        self.op.blank_file_conditions = {'Dox' : 1.0}
        self.op.estimate(ex_morpho, subset = 'Morpho1_2 == True')
        
    def testSubset(self):

        gm_1 = flow.GaussianMixtureOp(name = "Morpho1",
                                      channels = ["FSC-A", "SSC-A"],
                                      scale = {"SSC-A" : "log"},
                                      num_components = 2,
                                      sigma = 2)
        gm_1.estimate(self.ex)
        ex_morpho = gm_1.apply(self.ex)
        
        self.op.estimate(ex_morpho, subset = "Morpho1_2 == True")
        
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestAutofluorescence.testConditions']
    unittest.main()
        

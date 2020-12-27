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
Created on Nov 16, 2015

@author: brian
'''
import unittest
import pandas as pd
import cytoflow as flow
from test_base import ClosePlotsWhenDoneTest


class TestBleedthroughLinear(ClosePlotsWhenDoneTest):


    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {'Dox' : 'int'},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/rby.fcs',
                                                   conditions = {'Dox' : 10})]).apply()        
        
        self.op = flow.BleedthroughLinearOp(
                        controls = {"FITC-A" : self.cwd + '/data/tasbe/eyfp.fcs',
                                    "PE-Tx-Red-YG-A" : self.cwd + '/data/tasbe/mkate.fcs',
                                    "Pacific Blue-A" : self.cwd + '/data/tasbe/ebfp.fcs'})
            
        self.op.estimate(self.ex)
        
    def testEstimate(self):
        self.assertAlmostEqual(self.op.spillover[('FITC-A', 'Pacific Blue-A')], 0.0017542981896775413, places = 3)
        self.assertAlmostEqual(self.op.spillover[('FITC-A', 'PE-Tx-Red-YG-A')], 0.0096794979082161555, places = 3)
        self.assertAlmostEqual(self.op.spillover[('Pacific Blue-A', 'PE-Tx-Red-YG-A')], 0.0088300567877762134, places = 3)
        self.assertAlmostEqual(self.op.spillover[('Pacific Blue-A', 'FITC-A')], 0.00025201977142884287, places = 3)
        self.assertAlmostEqual(self.op.spillover[('PE-Tx-Red-YG-A', 'Pacific Blue-A')], 0.0007656573951714137, places = 3)
        self.assertAlmostEqual(self.op.spillover[('PE-Tx-Red-YG-A', 'FITC-A')], 0.0014315458081464413, places = 3)

    def testApply(self):
        ex2 = self.op.apply(self.ex)
        
        # make sure that SOMETHING changed.
        # TODO - check that the spillover was actually removed
        with self.assertRaises(AssertionError):
            pd.testing.assert_frame_equal(self.ex.data, ex2.data)
            
    def testApplyDoesntAlterOriginal(self):
        ex_data_copy = self.ex.data.copy(deep = True)
        self.op.apply(self.ex)
        
        pd.testing.assert_frame_equal(self.ex.data, ex_data_copy, check_like = True)
    
    def testPlot(self):
        self.op.default_view().plot(self.ex)
        
    def testConditions(self):
        self.op.control_conditions = {'FITC-A' : {'Dox' : 1},
                                      'PE-Tx-Red-YG-A' : {'Dox' : 1},
                                      'Pacific Blue-A' : {'Dox' : 1}}
        self.op.estimate(self.ex)

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestBleedthroughLinear.testEstimate']
    unittest.main()

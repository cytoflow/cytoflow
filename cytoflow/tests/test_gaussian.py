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
Created on Feb 4, 2018

@author: brian
'''
import unittest
import cytoflow as flow
from test_base import ImportedDataTest  # @UnresolvedImport

class TestGaussian(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)

        self.op = flow.GaussianMixtureOp(name = "GM",
                                         channels = ["V2-A", "Y2-A"],
                                         scale = {"V2-A" : "logicle",
                                                  "Y2-A" : "logicle"},
                                         num_components = 2)
        
    def testEstimate(self):
        self.op.estimate(self.ex)
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['GM'].unique()), 2)
        
    def testEstimateBy(self):
        self.op.by = ["Well"]
        self.op.estimate(self.ex)
        
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['GM'].unique()), 2)

    def testEstimateBy2(self):
        self.op.by = ["Well", "Dox"]
        self.op.estimate(self.ex)
        
        ex2 = self.op.apply(self.ex)
        self.assertEqual(len(ex2['GM'].unique()), 2)
        
    def testPlot(self):
        self.op.estimate(self.ex)
        self.op.default_view().plot(self.ex)

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestKMeans.testEstimateBy1Channel']
    unittest.main()
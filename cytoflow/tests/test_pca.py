#!/usr/bin/env python3.8
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
Created on Feb 4, 2018

@author: brian
'''
import unittest
import cytoflow as flow
import pandas as pd
from .test_base import ImportedDataSmallTest


class TestPCA(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.op = flow.PCAOp(name = "PCA",
                             channels = ["V2-A", "V2-H", "Y2-A", "Y2-H"],
                             scale = {"V2-A" : "log",
                                      "V2-H" : "log",
                                      "Y2-A" : "log",
                                      "Y2-H" : "log"},
                             num_components = 2)

        
    def testEstimate(self):
        self.op.estimate(self.ex)
        ex2 = self.op.apply(self.ex)
        self.assertIn("PCA_1", ex2.channels)
        self.assertIn("PCA_2", ex2.channels)
        
        self.assertIsInstance(ex2.data.index, pd.RangeIndex)
        
    def testEstimateBy(self):
        self.op.by = ["Dox"]
        self.op.estimate(self.ex)
        
        ex2 = self.op.apply(self.ex)

        self.assertIn("PCA_1", ex2.channels)
        self.assertIn("PCA_2", ex2.channels)
        
    def testWhiten(self):
        self.op.whiten = True
        self.op.estimate(self.ex)
        
        ex2 = self.op.apply(self.ex)

        self.assertIn("PCA_1", ex2.channels)
        self.assertIn("PCA_2", ex2.channels)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

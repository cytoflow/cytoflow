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
Created on April 10, 2023

@author: florian
'''
import unittest
import cytoflow as flow
import cytoflow.utility as util
import numpy as np
import umap
from .test_base import ImportedDataSingleTubeSmallTest
from sklearn.preprocessing import StandardScaler

        
class TestUMAP(ImportedDataSingleTubeSmallTest):
    def setUp(self):
        super().setUp()
        self.op = flow.UMAPOp(name = "UMAP",
                             channels = ["V2-A", "V2-H", "Y2-A", "Y2-H"],
                             scale = {"V2-A" : "log",
                                      "V2-H" : "log",
                                      "Y2-A" : "log",
                                      "V2-H" : "log"},
                             num_components = 2)

# region [positive tests]
    def testApplyUMAP_similarNamedUMAPAlreadyApplied_ThrowsCytoflowError(self):
        self.op.estimate(self.ex)
        ex1 = self.op.apply(self.ex)
        self.op.name = "UMAP2"
        ex2 = self.op.apply(ex1)
        self.assertIn("UMAP_1", ex2.channels)
        self.assertIn("UMAP2_1", ex2.channels)

    def testApplyUMAP_appliedTwiceToSameExperiment_ResultsInSameEmbedding(self):
        self.op.random_state = 10
        self.op.estimate(self.ex)
        ex1 = self.op.apply(self.ex)
        self.setUp()
        self.op.random_state = 10
        self.op.estimate(self.ex)
        ex2 = self.op.apply(self.ex)

        self.assertTrue(np.all(ex1.data["UMAP_1"] ==ex2.data["UMAP_1"]))
    
    def testApplyUMAP_appliedTwiceWithDifferentMinDist_ResultsDiffer(self):
        self.op.random_state = 10
        self.op.estimate(self.ex)
        ex1 = self.op.apply(self.ex)
        self.op.min_dist = 0.2
        self.op.estimate(self.ex)
        ex2 = self.op.apply(self.ex)
        self.assertNotEqual(ex1.data["UMAP_1"][0], ex2.data["UMAP_1"][0])

    def testApplyUMAP_appliedTwiceWithDifferentNumberOfNeighbors_ResultsDiffer(self):
        self.op.random_state = 10
        self.op.estimate(self.ex)
        ex1 = self.op.apply(self.ex)
        self.op.n_neighbors = 10
        self.op.estimate(self.ex)
        ex2 = self.op.apply(self.ex)
        self.assertNotEqual(ex1.data["UMAP_1"][0], ex2.data["UMAP_1"][0])

# endregion

# region [negative tests]
    def testApplyUMAP_similarNamedUMAPAlreadyApplied_ThrowsCytoflowError(self):
        self.op.estimate(self.ex)
        ex1 = self.op.apply(self.ex)
        with self.assertRaises(util.CytoflowOpError):
            ex2 = self.op.apply(ex1)
    
    def testApplyUMAP_wrongDataColumnsAppliedToUMAP_ThrowsCytoflowError(self):
        self.op.estimate(self.ex)
        self.ex.data.rename(columns = {"V2-A" : "V2-A2"}, inplace = True)

        with self.assertRaises(util.CytoflowError):
            self.op.apply(self.ex)

# endregion

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

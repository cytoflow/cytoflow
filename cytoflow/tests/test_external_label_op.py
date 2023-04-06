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
import cytoflow.utility as util
import pandas as pd
from traits.trait_errors import TraitError


class TestExternalLabel(unittest.TestCase):
    def setUp(self):
        super().setUp()
        
        tube1 = flow.Tube(file = './cytoflow/tests/data/vie14/494.fcs')
        self.ex = flow.ImportOp(tubes = [tube1]).apply()

    # region [postive tests]

    def testApplyLabel_ValidDataFrameGiven_LabelsArePresentInExperiment(self):
        labels_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
        labels = flow.ExternalLabelOp(labels = labels_df)
        new_ex = labels.apply(self.ex)
        self.assertTrue("blast" in new_ex.data.columns)

    def testApplyLabel_CorrectPathGiven_LabelsArePresentInExperiment(self):
        labels = flow.ExternalLabelOp(labels_csv_path = './cytoflow/tests/data/vie14/494_labels.csv')
        new_ex = labels.apply(self.ex)
        self.assertTrue("blast" in new_ex.data.columns)

    # endregion

    #region [negative tests]

    def testApplyLabel_NoLabelsGiven_ThrowsTraitError(self):
        with self.assertRaises(util.CytoflowOpError):
            labels = flow.ExternalLabelOp()
            new_ex = labels.apply(self.ex)

    def testApplyLabel_NumpyGiven_ThrowsTraitError(self):
        with self.assertRaises(TraitError):
            labels_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
            labels = flow.ExternalLabelOp(labels = labels_df.to_numpy())
            new_ex = labels.apply(self.ex)
        
        

    def testApplyLabel_NonExistingPathGiven_ThrowsCytoFlowOpException(self):
        with self.assertRaises(util.CytoflowOpError):
            labels = flow.ExternalLabelOp(labels_csv_path = './cytoflow/tests/data/vie14/typo.csv')
            new_ex = labels.apply(self.ex)
    
    # endregion


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
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
import pandas as pd
from traits.trait_errors import TraitError


class TestBulkCondition(unittest.TestCase):
    def setUp(self):
        super().setUp()
        
        tube1 = flow.Tube(file = './cytoflow/tests/data/vie14/494.fcs')
        self.ex = flow.ImportOp(tubes = [tube1]).apply()

    # region [postive tests]

    def testApplyCondition_ValidDataFrameGiven_ConditionsArePresentInExperiment(self):
        conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
        cond_op = flow.BulkConditionOp(conditions_df = conditions_df)
        new_ex = cond_op.apply(self.ex)
        self.assertTrue("blast" in new_ex.data.columns)

    def testApplyCondition_CorrectPathGiven_ConditionsArePresentInExperiment(self):
        cond_op = flow.BulkConditionOp(conditions_csv_path = './cytoflow/tests/data/vie14/494_labels.csv')
        new_ex = cond_op.apply(self.ex)
        self.assertTrue("blast" in new_ex.data.columns)

    def testApplyCondition_EmptyCombineOrderGiven_NoCombineColumnCreated(self):
        cond_op = flow.BulkConditionOp(conditions_csv_path = './cytoflow/tests/data/vie14/494_labels.csv')
        new_ex = cond_op.apply(self.ex)
        self.assertTrue("blast" in new_ex.data.columns)
        self.assertTrue("combined_conditions" not in new_ex.data.columns)

    def testApplyCondition_CombineOrderGiven_CorrectCombineValueIsPresentForFirstTwoMeasurement(self):
        conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
        cond_op = flow.BulkConditionOp(conditions_df = conditions_df, combine_order = ["allevents","syto", "singlets", "intact","cd19", "blast"])
        new_ex = cond_op.apply(self.ex)
        self.assertEqual(new_ex.data['combined_conditions'][0],'allevents')
        self.assertEqual(new_ex.data['combined_conditions'][1],'blast')
        self.assertEqual(new_ex.metadata['combined_conditions']["dtype"], 'category')

    def testApplyCondition_DifferentCombineConditionsNameGiven_CorrectColumnNameIsPresent(self):
        conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
        cond_op = flow.BulkConditionOp(conditions_df = conditions_df, combine_order = ["allevents","syto", "singlets", "intact","cd19", "blast"])
        cond_op.combined_conditions_name = "combined"
        new_ex = cond_op.apply(self.ex)
        self.assertTrue("combined" in new_ex.data.columns)
        self.assertTrue("combined_conditions" not in new_ex.data.columns)
        self.assertEqual(new_ex.data['combined'][0],'allevents')

    def testApplyCondition_DifferentCombineDefaultValueGiven_CorrectDefaultValueIsPresent(self):
        conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
        cond_op = flow.BulkConditionOp(conditions_df = conditions_df, combine_order = ["cd19", "blast"])
        cond_op.combined_condition_default = "default"
        new_ex = cond_op.apply(self.ex)
        self.assertEqual(new_ex.data['combined_conditions'][0],'default')
        self.assertEqual(new_ex.data['combined_conditions'][1],'blast')

    # endregion

    #region [negative tests]

    def testApplyCondition_NoLabelsGiven_ThrowsTraitError(self):
        with self.assertRaises(util.CytoflowOpError):
            cond_op = flow.BulkConditionOp()
            new_ex = cond_op.apply(self.ex)

    def testApplyCondition_NumpyGiven_ThrowsTraitError(self):
        with self.assertRaises(TraitError):
            conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
            cond_op = flow.BulkConditionOp(conditions_df = conditions_df.to_numpy())
            new_ex = cond_op.apply(self.ex)
        
    def testApplyCondition_NonExistingPathGiven_ThrowsCytoFlowOpException(self):
        with self.assertRaises(util.CytoflowOpError):
            cond_op = flow.BulkConditionOp(conditions_csv_path = './cytoflow/tests/data/vie14/typo.csv')
            new_ex = cond_op.apply(self.ex)

    def testApplyCondition_NonExistingColumnInCombineOrderGiven_ThrowsCytoFlowOpException(self):
        with self.assertRaises(util.CytoflowOpError):
            conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
            cond_op = flow.BulkConditionOp(conditions_df = conditions_df, combine_order = ['blasts','typo'])
            new_ex = cond_op.apply(self.ex)
    
    def testApplyCondition_DuplicateColumnInCombineOrderGiven_ThrowsCytoFlowOpException(self):
        conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
        with self.assertRaises(util.CytoflowOpError):
            cond_op = flow.BulkConditionOp(conditions_df = conditions_df, combine_order = ['blasts','blasts'])
            new_ex = cond_op.apply(self.ex)

    def testApplyCondition_HasAlreadyBeenApplied_ThrowsCytoFlowOpException(self):
        conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
        cond_op = flow.BulkConditionOp(conditions_df = conditions_df)
        new_ex = cond_op.apply(self.ex)
        with self.assertRaises(util.CytoflowOpError):
            new_ex2 = cond_op.apply(new_ex)

    # endregion


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
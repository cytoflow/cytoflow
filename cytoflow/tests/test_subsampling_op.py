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
Created on April 12, 2023

@author: florian
'''
import unittest

import numpy as np
import cytoflow as flow
import cytoflow.utility as util
import pandas as pd


class TestSubsampleOp(unittest.TestCase):
    def setUp(self):
        super().setUp()
        
        tube1 = flow.Tube(file = './cytoflow/tests/data/vie14/494.fcs')
        org_ex = flow.ImportOp(tubes = [tube1]).apply()
        cond_op = flow.BulkConditionOp(conditions_csv_path = './cytoflow/tests/data/vie14/494_labels.csv',
                                        combine_order = ["allevents","syto", "singlets", "intact","cd19", "blast"])
        cond_op.combined_conditions_name = "label"
        self.ex = cond_op.apply(org_ex)

    # region [postive tests]
    
    def testApplySampling_AbsoluteRandomSampling_CorrectNumberOfEventsGiven(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_size = 100)
        new_ex = subsampling_op.apply(self.ex)
        self.assertEqual(new_ex.data.shape[0], 100)

    def testApplySampling_RelativeRandomSampling_CorrectNumberOfEventsGiven(self):
        n_events = self.ex.data.shape[0]
        subsampling_op = flow.SubsampleOp(sampling_type = "relative", sampling_size = 0.1)
        new_ex = subsampling_op.apply(self.ex)
        self.assertEqual(new_ex.data.shape[0], int(np.round(n_events * 0.1)))

    def testApplySampling_AbsoluteSamplingPerConditionValue_CorrectNumberOfEventsGiven(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_def = {
            "label" : {"blast" : 200, "cd19" : 100}
        })
        new_ex = subsampling_op.apply(self.ex)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "blast"]), 200)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "cd19"]), 100)
    
    def testApplySampling_AbsoluteSamplingPerConditionWithoutReplacement_LessNumberOfEventsThanConfiguredGiven(self):
        n_blast = len(self.ex.data[self.ex.data["label"] == "blast"])
        n_blast_wanted = 2*n_blast
        self.assertGreater(n_blast_wanted, n_blast)

        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_def = {
            "label" : {"blast" : n_blast_wanted, "cd19" : 100}
        }, replacement = False)
        new_ex = subsampling_op.apply(self.ex)

        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "blast"]), n_blast)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "cd19"]), 100)

    def testApplySampling_AbsoluteSamplingPerConditionWithReplacement_LessNumberOfEventsThanConfiguredGiven(self):
        n_blast = len(self.ex.data[self.ex.data["label"] == "blast"])
        n_blast_wanted = 2*n_blast
        self.assertGreater(n_blast_wanted, n_blast)

        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_def = {
            "label" : {"blast" : n_blast_wanted, "cd19" : 100}
        }, replacement = True)
        new_ex = subsampling_op.apply(self.ex)

        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "blast"]), 2*n_blast)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "cd19"]), 100)
    
    def testApplySampling_RelativeSamplingPerConditionValue_CorrectNumberOfEventsGiven(self):
        n_blast = len(self.ex.data[self.ex.data["label"] == "blast"])
        n_cd19 = len(self.ex.data[self.ex.data["label"] == "cd19"])
        subsampling_op = flow.SubsampleOp(sampling_type = "relative", sampling_def = {
            "label" : {"blast" : 0.5, "cd19" : 0.1}
        })
        new_ex = subsampling_op.apply(self.ex)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "blast"]), np.round(0.5 *n_blast))
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "cd19"]), np.round(0.1 *n_cd19))
    
    def testApplySampling_AbsoluteSamplingFromEach_CorrectNumberOfEventsGiven(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_def = {
            "label" : "100:FromEach"
        })
        new_ex = subsampling_op.apply(self.ex)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "blast"]), 100)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "cd19"]), 100)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "singlets"]), 100)
    
    def testApplySampling_RelativSamplingFromEach_CorrectNumberOfEventsGiven(self):
        n_blast = len(self.ex.data[self.ex.data["label"] == "blast"])
        n_cd19 = len(self.ex.data[self.ex.data["label"] == "cd19"])
        n_singlets = len(self.ex.data[self.ex.data["label"] == "singlets"])

        subsampling_op = flow.SubsampleOp(sampling_type = "relative", sampling_def = {
            "label" : "0.2:FromEach"
        })
        new_ex = subsampling_op.apply(self.ex)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "blast"]), np.round(0.2 *n_blast))
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "cd19"]), np.round(0.2*n_cd19))
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "singlets"]), np.round(0.2*n_singlets))
    
    def testApplySampling_RelativSamplingInTotal_CorrectNumberOfEventsGiven(self):
        n_events = self.ex.data.shape[0]
        subsampling_op = flow.SubsampleOp(sampling_type = "relative", sampling_def = {
            "label" : "0.2:InTotal"
        })
        new_ex = subsampling_op.apply(self.ex)
        self.assertTrue(abs(new_ex.data.shape[0] - np.round(0.2 *n_events)) < 3)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "blast"]), len(new_ex.data[new_ex.data["label"] == "cd19"]))

    def testApplySampling_RelativSamplingInTotal_CorrectNumberOfEventsGiven(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_def = {
            "label" : "200:InTotal"
        })
        new_ex = subsampling_op.apply(self.ex)
        n_unqiue_labels = len(self.ex.data["label"].unique())
        self.assertTrue(abs(new_ex.data.shape[0] - 200) < n_unqiue_labels + 1)
        self.assertEqual(len(new_ex.data[new_ex.data["label"] == "blast"]), len(new_ex.data[new_ex.data["label"] == "cd19"]))


    # endregion

    #region [negative tests]


    def testApplySampling_ValueConfiguredNotPresentInExperiment_ThrowException(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_def = {
            "label" : {"blast" : 200, "cd19" : 100, "typo" : 100}
        })
        with self.assertRaises(util.CytoflowOpError):
            subsampling_op.apply(self.ex)

    def testApplySampling_WrongAggregateTypeGiven_ThrowsCytoflowError(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "relative", sampling_def = {
            "label" : "0.2:equallyPerTypo"
        })
        with self.assertRaises(util.CytoflowOpError):
            subsampling_op.apply(self.ex)

    def testApplySampling_NegativeAmountInSamplingDef_ThrowsCytoflowError(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_def = {
            "label" : {"blast" : 200, "cd19" : -100}
        })
        with self.assertRaises(util.CytoflowOpError):
            subsampling_op.apply(self.ex)

    def testApplySampling_NegativeAmountInSamplingSize_ThrowsCytoflowError(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_size = -100)
        with self.assertRaises(util.CytoflowOpError):
            subsampling_op.apply(self.ex)
    
    def testApplySampling_SamplingSizeAndSamplingDefGiven_ThrowsCytoflowError(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute", sampling_size = 100, sampling_def = {
            "label" : {"blast" : 200, "cd19" : 100}
        })
        with self.assertRaises(util.CytoflowOpError):
            subsampling_op.apply(self.ex)

    def testApplySampling_NeitherSamplingSizeNorSamplingDefGiven_ThrowsCytoflowError(self):
        subsampling_op = flow.SubsampleOp(sampling_type = "absolute")
        with self.assertRaises(util.CytoflowOpError):
            subsampling_op.apply(self.ex)

    #non categorical condition?

    # endregion


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
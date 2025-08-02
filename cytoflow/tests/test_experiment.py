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
from cytoflow import utility as util
import pandas as pd
from .test_base import ImportedDataTest

class TestExperiment(ImportedDataTest):
    def testConditions(self):
        self.assertEqual(len(self.ex['Dox'].unique()), 3)
        self.assertEqual(len(self.ex['Well'].unique()), 3)
        
    def testAddChannel(self):
        self.assertEqual(len(self.ex.channels), 16)
        self.ex.add_channel("FSC_over_2", self.ex.data["FSC-A"] / 2.0)
        self.assertEqual(len(self.ex.channels), 17)
        
    def testAddConflictingNameChannel(self):
        self.assertEqual(len(self.ex.channels), 16)
        with self.assertRaises(util.CytoflowError):
            self.ex.add_channel("B1_A", self.ex.data["FSC-A"] / 2.0)
        
    def testAddCondition(self):
        self.assertEqual(len(self.ex.conditions), 3)
        self.ex.add_condition('in_gate', 'bool', pd.Series([True] * len(self.ex)))
        self.assertEqual(len(self.ex.conditions), 4)

    def testAddConflictingNameCondition(self):
        self.assertEqual(len(self.ex.conditions), 3)
        with self.assertRaises(util.CytoflowError):
            self.ex.add_condition('B1_A', 'bool', pd.Series([True] * len(self.ex)))
    
    def testSubset(self):
        ex2 = self.ex.subset(['Dox', 'Well'], (10.0, 'C'))
        self.assertEqual(len(ex2['Dox'].unique()), 1)
        self.assertEqual(len(ex2['Well'].unique()), 1)
        self.assertEqual(len(ex2), 100)

    def testSubset2(self):
        ex2 = self.ex.subset('Dox', 100.0)
        self.assertEqual(len(ex2['Dox'].unique()), 1)
        self.assertEqual(len(ex2['Well'].unique()), 2)
        self.assertEqual(len(ex2), 200)
        
    def testQuery(self):
        ex2 = self.ex.query('Dox == 10.0 and Well == "C"')
        self.assertEqual(len(ex2['Dox'].unique()), 1)
        self.assertEqual(len(ex2['Well'].unique()), 1)
        self.assertEqual(len(ex2), 100)
        
    def testAddEvents(self):
        ex2 = self.ex.subset(['Dox', 'Well'], (10.0, 'C'))
        old_len = len(self.ex)
        
        self.ex.add_events(ex2.data[ex2.channels], {'Dox' : 1000.0, 
                                                    'Well' : 'D',
                                                    'bucket' : 1})
        
        self.assertEqual(len(self.ex['Dox'].unique()), 4)
        self.assertEqual(len(self.ex['Well'].unique()), 4)
        self.assertEqual(len(self.ex), len(ex2) + old_len)
        
    
    def testCloneIsShallow(self):
        ex2 = self.ex.clone(deep = False)
        self.assertNotEqual(self.ex['B1-A'].at[100], 100.0)
        ex2['B1-A'].at[100] = 100.0
        self.assertEqual(self.ex['B1-A'].at[100], 100.0)
         
    def testReplaceColumn(self):
        # clone self.ex; replace column B1-A with [100.0] * len(self.ex) in clone;
        # check that self.ex hasn't changed
         
        ex2 = self.ex.clone(deep = True)
        self.assertNotEqual(self.ex['B1-A'].at[100], 100.0)
        s = pd.Series([100.0] * len(self.ex))
         
        ex2.data['B1-A'] = s
         
        self.assertEqual(ex2['B1-A'].at[100], 100.0)
        self.assertNotEqual(self.ex['B1-A'].at[100], 100.0)
        
        
    def testPickle(self):
        import pickle, pandas.testing
        ex2 = pickle.loads(pickle.dumps(self.ex))
        
        pandas.testing.assert_frame_equal(self.ex.data, ex2.data)
        self.assertDictEqual(self.ex.metadata, ex2.metadata)
        # self.assertDictEqual(self.ex.statistics, ex2.statistics)
        for s in self.ex.statistics:
            pandas.testing.assert_frame_equal(self.ex.statistics[s],
                                              ex2.statistics[s])
        self.assertListEqual([x.id for x in self.ex.history], 
                             [x.id for x in ex2.history])

        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'TestExperiment.testSubset2']
    unittest.main()

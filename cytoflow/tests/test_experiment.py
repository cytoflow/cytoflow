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
Created on Dec 1, 2015

@author: brian
'''
import unittest
import os
import cytoflow as flow
import pandas as pd
from test_base import ImportedDataSmallTest


class TestExperiment(ImportedDataSmallTest):
    def testConditions(self):
        self.assertEqual(len(self.ex['Dox'].unique()), 2)
        self.assertEqual(len(self.ex['Well'].unique()), 2)
        
    def testAddChannel(self):
        # TODO
        pass
        
    def testAddCondition(self):
        # TODO
        pass
    
#     def testCloneIsShallow(self):
#         ex2 = self.ex.clone()
#         self.assertNotEqual(self.ex['B1-A'].at[100], 100.0)
#         ex2['B1-A'].at[100] = 100.0
#         self.assertEqual(self.ex['B1-A'].at[100], 100.0)
#         
#     def testReplaceColumn(self):
#         # clone self.ex; replace column B1-A with [100.0] * len(self.ex) in clone;
#         # check that self.ex hasn't changed; check that B1-H is still shallow.
#         
#         ex2 = self.ex.clone()
#         self.assertNotEqual(self.ex['B1-A'].at[100], 100.0)
#         s = pd.Series([100.0] * len(self.ex))
#         
#         # ex2.data['B1-A'] = s
#         # nope, updates self.ex    
#     
#         # ex2.data = self.ex.data.assign(**{'B1-A': s})
#         # nope, gives a deep copy
#         
#         self.assertEqual(ex2['B1-A'].at[100], 100.0)
#         self.assertNotEqual(self.ex['B1-A'].at[100], 100.0)
#         
#         self.assertNotEqual(self.ex['B1-H'].at[100], 100.0)
#         ex2.data['B1-H'].at[100] = 100.0
#         self.assertEqual(self.ex['B1-H'].at[100], 100.0)
#         
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

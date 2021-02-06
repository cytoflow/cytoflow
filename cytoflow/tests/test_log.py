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
Created on Dec 1, 2015

@author: brian
'''
import unittest
import os

import pandas as pd

import cytoflow as flow
import cytoflow.utility as util

class Test(unittest.TestCase):
    
    def setUp(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/mkate.fcs',
                                                   conditions = {})]).apply()
        

    def test_run(self):
        scale = util.scale_factory("log", self.ex, channel = "Pacific Blue-A")
        x = scale(20.0)
        self.assertTrue(isinstance(x, float))
        
        x = scale([20])
        self.assertTrue(isinstance(x, list))
        
        x = scale(pd.Series([20]))
        self.assertTrue(isinstance(x, pd.Series))
                        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
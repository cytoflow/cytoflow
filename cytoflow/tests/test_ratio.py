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
import pandas as pd
import cytoflow.utility as util
from .test_base import ImportedDataSmallTest


class TestChannelRatio(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.ex = flow.RatioOp(name = "R",
                               numerator = "Y2-A",
                               denominator = "V2-A").apply(self.ex)
        
    def testApply(self):   
        self.assertIn("R", self.ex.channels)
        
                
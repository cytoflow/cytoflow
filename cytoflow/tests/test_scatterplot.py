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
Created on Mar 5, 2018

@author: brian
'''

import unittest

import cytoflow as flow

from .test_base import View2DTestBase


class TestScatterplot(View2DTestBase, unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.view = flow.ScatterplotView(xchannel = "B1-A",
                                         ychannel = "Y2-A")

    # scatterplot params
    
    def testAlpha(self):
        self.view.plot(self.ex, alpha = 0.1)
        
    def testSize(self):
        self.view.plot(self.ex, s = 5)
        
    def testMarker(self):
        for mk in ["o", ",", "v", "^", "<", ">", "1", "2", "3", "4", "8",
                       "s", "p", "*", "h", "H", "+", "x", "D", "d", ""]:
            self.view.plot(self.ex, marker = mk)
        
        
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

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
import cytoflow as flow
from test_base import ImportedDataSmallTest  # @UnresolvedImport

class Test(ImportedDataSmallTest):
    def setUp(self):
        super().setUp()
        self.gate = flow.RangeOp(name = "Range",
                                 channel = "Y2-A",
                                 low = 1000,
                                 high = 10000)
        
    def testGate(self):
        ex2 = self.gate.apply(self.ex)
        
        # how many events ended up in the gate?
        self.assertEqual(ex2.data.groupby("Range").size()[True], 4111)

    def testPlot(self):
        self.gate.default_view().plot(self.ex)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

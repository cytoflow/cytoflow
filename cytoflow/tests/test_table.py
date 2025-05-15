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

import unittest, tempfile, os
import cytoflow as flow
import cytoflow.utility as util

from .test_base import ImportedDataTest

class TestTable(ImportedDataTest):

    def setUp(self):
        ImportedDataTest.setUp(self)
        self.ex = flow.ThresholdOp(name = "T",
                                   channel = "Y2-A",
                                   threshold = 500).apply(self.ex)

        self.ex = flow.ChannelStatisticOp(name = "ByDox",
                             channel = "Y2-A",
                             by = ['Dox'],
                             function = flow.geom_mean).apply(self.ex)
                             
        self.ex = flow.ChannelStatisticOp(name = "ByDoxWell",
                             channel = "Y2-A",
                             by = ['Dox', 'Well'],
                             function = flow.geom_mean).apply(self.ex)
                                 
        with self.assertWarns(util.CytoflowOpWarning):
            self.ex = flow.ChannelStatisticOp(name = "ByDoxWellT",
                                 channel = "Y2-A",
                                 by = ['Dox', 'Well', 'T'],
                                 fill = 0.0,
                                 function = flow.geom_mean).apply(self.ex)
                                 
    def tearDown(self):
        fh, filename = tempfile.mkstemp()
        
        try:
            os.close(fh)
            self.view.export(self.ex, filename)
        finally:
            os.unlink(filename)

        
    def testPlotRowSubset(self):
        self.view = flow.TableView(statistic = "ByDox",
                                   feature = "Y2-A",
                                   row_facet = "Dox",
                                   subset = "Dox > 1")
        self.view.plot(self.ex)
        
    def testPlotRow(self):
        self.view = flow.TableView(statistic = "ByDox",
                                   feature = "Y2-A",
                                   row_facet = "Dox")
        self.view.plot(self.ex)
        
    def testPlotSubrow(self):
        self.view = flow.TableView(statistic = "ByDoxWell",
                                   feature = "Y2-A",
                                   row_facet = 'Dox',
                                   subrow_facet = 'Well')
        self.view.plot(self.ex)
        
    def testPlotColumn(self):
        self.view = flow.TableView(statistic = "ByDox",
                                   feature = "Y2-A",
                                   column_facet = "Dox")
        self.view.plot(self.ex)
        
    def testPlotSubcolumn(self):
        self.view = flow.TableView(statistic = "ByDoxWell",
                                   feature = "Y2-A",
                                   column_facet = 'Dox',
                                   subcolumn_facet = 'Well')
        self.view.plot(self.ex)

    def testPlotRowAndColumn(self):
        self.view = flow.TableView(statistic = "ByDoxWell",
                                   feature = "Y2-A",
                                   row_facet = 'Dox',
                                   column_facet = 'Well')
        self.view.plot(self.ex)        

        

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestTable.testPlotColumnRange']
    unittest.main()

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
import unittest, os, tempfile, shutil
import cytoflow as flow
from test_base import ImportedDataSmallTest


class Test(ImportedDataSmallTest):

    def setUp(self):
        super().setUp()
        self.directory = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.directory)
        
    def testRoundtrip(self):
        flow.ExportFCS(path = self.directory,
                       by = ['Dox']).export(self.ex)
                       
        tube1 = flow.Tube(file = self.directory + '/Dox_10.0.fcs', 
                          conditions = {"Dox" : 10.0})
        tube2 = flow.Tube(file = self.directory + '/Dox_1.0.fcs',
                          conditions = {"Dox" : 1.0})
        
        ex_rt = flow.ImportOp(conditions = {"Dox" : "float"},
                              tubes = [tube1, tube2]).apply()

        self.assertTrue((self.ex.data == ex_rt.data).all().all())

        for channel in self.ex.channels:
            self.assertEqual(self.ex.metadata[channel]['range'],
                             ex_rt.metadata[channel]['range'])


    def testRoundtripWithBeadCalibration(self):
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {'Dox' : 'float'},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/rby.fcs',
                                                   conditions = {'Dox' : 1.0})]).apply()        
        
        op = flow.BeadCalibrationOp(
                    units = {"PE-Tx-Red-YG-A" : "MEPTR"},
                    beads_file = self.cwd + '/data/tasbe/beads.fcs',
                    beads = flow.BeadCalibrationOp.BEADS["Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R"])
        op.estimate(self.ex)
        
        ex2 = op.apply(self.ex)
        
        flow.ExportFCS(path = self.directory, by = ['Dox']).export(ex2)   
        
        tube1 = flow.Tube(file = self.directory + '/Dox_1.0.fcs', 
                          conditions = {"Dox" : 1.0})
        ex_rt = flow.ImportOp(conditions = {'Dox' : 'float'},
                              tubes = [tube1]).apply()
                              
        self.assertNotIn('voltage', ex_rt.metadata['PE-Tx-Red-YG-A'])             

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

#!/usr/bin/env python3.6
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
Created on Mar 7, 2018

@author: brian
'''

import unittest, os

import cytoflow as flow


class ClosePlotsWhenDoneTestCase(unittest.TestCase):
    def tearDown(self):
        """Run once after each test"""
        import matplotlib.pyplot
        matplotlib.pyplot.close('all')


class ImportedDataTest(ClosePlotsWhenDoneTestCase):
    def setUp(self, thin=100):
        """Run once per test at the beginning"""
        from cytoflow import Tube
        
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
     
        tube1 = Tube(file = self.cwd + "CFP_Well_A4.fcs",
                     conditions = {"Dox" : 0.0, "Well" : 'Aa'})
     
        tube2 = Tube(file = self.cwd + "RFP_Well_A3.fcs",
                     conditions = {"Dox" : 10.0, "Well" : 'Aa'})

        tube3 = Tube(file = self.cwd + "YFP_Well_A7.fcs",
                     conditions = {"Dox" : 100.0, "Well" : 'Aa'})
         
        tube4 = Tube(file = self.cwd + "CFP_Well_B4.fcs",
                     conditions = {"Dox" : 0.0, "Well" : 'Bb'})
     
        tube5 = Tube(file = self.cwd + "RFP_Well_A6.fcs",
                     conditions = {"Dox" : 10.0, "Well" : 'Bb'})

        tube6 = Tube(file = self.cwd + "YFP_Well_C7.fcs",
                     conditions = {"Dox" : 100.0, "Well" : 'Bb'})

        tube7 = Tube(file = self.cwd + "CFP_Well_B4.fcs",
                     conditions = {"Dox" : 0.0, "Well" : 'Cc'})
     
        tube8 = Tube(file = self.cwd + "RFP_Well_A6.fcs",
                     conditions = {"Dox" : 10.0, "Well" : 'Cc'})

        tube9 = Tube(file = self.cwd + "YFP_Well_C7.fcs",
                     conditions = {"Dox" : 100.0, "Well" : 'Cc'})
        
        self.ex = flow.ImportOp(conditions = {"Dox" : "float", "Well" : "category"},
                                tubes = [tube1, tube2, tube3,
                                         tube4, tube5, tube6,
                                         tube7, tube8, tube9]).apply()
        if thin > 1:
            import numpy as np
            # thin the dataset 100-fold from 90k to 900 rows for thin=100
            self.ex.add_condition("bucket", "int", np.arange(self.ex.data.shape[0]) % thin)
            self.ex = self.ex.query("bucket == 0")


class ImportedDataSmallTest(ClosePlotsWhenDoneTestCase):
    def setUp(self):
        """Run once per test at the beginning"""
        from cytoflow import Tube

        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
        tube1 = flow.Tube(file=self.cwd + 'RFP_Well_A3.fcs', conditions={"Dox": 10.0})
        tube2 = flow.Tube(file=self.cwd + 'CFP_Well_A4.fcs', conditions={"Dox": 1.0})
        import_op = flow.ImportOp(conditions={"Dox": "float"},
                                  tubes=[tube1, tube2])
        self.ex = import_op.apply()


class TasbeTest(ClosePlotsWhenDoneTestCase):
    
    def setUp(self):
        """Run once at the beginning of each test"""

        from cytoflow import Tube
             
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/tasbe/"
     
        tube = Tube(file = self.cwd + "rby.fcs")
        
        self.ex = flow.ImportOp(tubes = [tube])

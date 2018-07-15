#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
Created on Nov 16, 2015

@author: brian
'''
import unittest
import cytoflow as flow

class Test(unittest.TestCase):


    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {'Dox' : 'int'},
                                tubes = [flow.Tube(file = self.cwd + '/data/tasbe/mkate.fcs',
                                                   conditions = {'Dox' : 3})]).apply()        
        
        self.op = flow.ColorTranslationOp(
                        controls = {("PE-Tx-Red-YG-A", "FITC-A") :
                                    self.cwd + '/data/tasbe/rby.fcs',
                                    ("Pacific Blue-A", "FITC-A") :
                                    self.cwd + '/data/tasbe/rby.fcs'},
                        mixture_model = True)
            
        self.op.estimate(self.ex)

    def test_apply(self):
        ex2 = self.op.apply(self.ex)
        
        with self.assertRaises(ValueError):
            self.assertFalse((self.ex.data == ex2.data).all().all())
    
    def test_plot(self):
        self.op.default_view().plot(self.ex)
        
    def test_conditions(self):
        self.op.control_conditions = {("PE-Tx-Red-YG-A", "FITC-A") : {'Dox' : 1},
                                      ("Pacific Blue-A", "FITC-A") : {'Dox' : 1}}
        self.op.estimate(self.ex)
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
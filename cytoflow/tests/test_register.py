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
Created on Nov 15, 2015

@author: brian
'''

import unittest
import cytoflow as flow
import pandas as pd

class TestRegistration(unittest.TestCase):

    def setUp(self):
        import os
        self.cwd = os.path.dirname(os.path.abspath(__file__))
        self.ex = flow.ImportOp(conditions = {'Sample' : 'category'},
                                tubes = [flow.Tube(file = self.cwd + '/data/module_examples/itn_02.fcs', conditions = {'Sample' : 2}),
                                         flow.Tube(file = self.cwd + '/data/module_examples/itn_03.fcs', conditions = {'Sample' : 3})],
                                channels = {'CD3' : 'CD3', 
                                            'CD4' : 'CD4'}).apply()        
        
        self.op = flow.RegistrationOp(channels = ["CD3", "CD4"],
                                      scale = {"CD3" : "log",
                                               "CD4" : "log"},
                                      by = ["Sample"])
        self.op.estimate(self.ex)

    def testWarp(self):
        # checked the correctness of this warp visually
        
        correct_peaks = {'CD3': {(2,): [1.08783492527716, 12.142584261984755, 440.3015356513047],
                                 (3,): [1.08783492527716, 4.678268264317964, 351.7914321296273]},
                         'CD4': {(2,): [1.0146340570192034, 9.180246637211349, 46.75906376829905, 162.37592106463455],
                                 (3,): [1.0146340570192034, 9.180246637211349, 147.5477931840344]}}
        
        for channel in correct_peaks:
            for group in correct_peaks[channel]:
                for i in range(len(correct_peaks[channel][group])):
                    self.assertAlmostEqual(self.op._peaks[channel][group][i], 
                                           correct_peaks[channel][group][i])
                
        correct_clusters = {'CD3': {(2,): [0, 2, 1], (3,): [0, 2, 1]},
                            'CD4': {(3,): [1, 2, 0], (2,): [1, 2, None, 0]}}
        
        for channel in correct_clusters:
            for group in correct_clusters[channel]:
                for i in range(len(correct_clusters[channel][group])):
                    self.assertEqual(self.op._clusters[channel][group][i], 
                                    correct_clusters[channel][group][i])
        
        correct_means = {'CD3': [1.08783492527716, 393.566141576796, 7.536993206819948],
                         'CD4': [154.7843946246255, 1.0146340570192034, 9.180246637211349, None]}
        
        for channel in correct_means:
                for i in range(len(correct_means[channel])):
                    self.assertAlmostEqual(self.op._means[channel][i], 
                                           correct_means[channel][i])
        
        

        
    def testLogicle(self):
        self.op.scale = {"CD3" : "logicle",
                         "CD4" : "logicle"}
        self.op.estimate(self.ex)
        self.op.default_view().plot(self.ex, plot_name = "CD3")
        self.op.default_view().plot(self.ex, plot_name = "CD4")

    def testApply(self):
        # this is just to make sure the code doesn't crash;
        # nothing about correctness.
    
        ex2 = self.op.apply(self.ex)  
        self.assertIsInstance(ex2.data.index, pd.RangeIndex)
    #
    def testPlot(self):
        # this is to make sure the code doesn't crash;
        # nothing about correctness
    
        self.op.default_view().plot(self.ex, plot_name = "CD3")
        self.op.default_view().plot(self.ex, plot_name = "CD4")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()

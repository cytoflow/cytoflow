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

import unittest
import pandas as pd

import cytoflow as flow
import cytoflow.utility as util

from .test_base import ImportedDataTest

class TestMST(ImportedDataTest):

    def setUp(self):
        super().setUp()
        
        km = flow.KMeansOp(name = "KMeans",
                           channels = ["V2-A", "Y2-A", "B1-A"],
                           scale = {"V2-A" : "logicle",
                                    "Y2-A" : "logicle",
                                    "B1-A" : "logicle"},
                           num_clusters = 20)
        km.estimate(self.ex)
                   
        self.ex = km.apply(self.ex)
                                          
        self.view = flow.MSTView(statistic = "DoxLen", 
                                 locations = "KMeans", 
                                 locations_features = ["V2-A", "Y2-A", "B1-A"],
                                 feature = "Y2-A",
                                 size_function = len)
        
    def testHeat(self):
        self.ex = flow.ChannelStatisticOp(name = "DoxLen",
                                          channel = "Y2-A",
                                          by = ["KMeans"],
                                          function = len).apply(self.ex)
        self.view.style = "heat"
        self.view.plot(self.ex)
        
    def testPie(self):
        self.ex = flow.ChannelStatisticOp(name = "DoxLen",
                                          channel = "Y2-A",
                                          by = ["KMeans", "Dox"],
                                          function = len).apply(self.ex)
        self.view.style = "pie"
        self.view.variable = "Dox"
        self.view.plot(self.ex)

    def testPetal(self):
        self.ex = flow.ChannelStatisticOp(name = "DoxLen",
                                          channel = "Y2-A",
                                          by = ["KMeans", "Dox"],
                                          function = len).apply(self.ex)
        self.view.style = "petal"
        self.view.variable = "Dox"
        self.view.plot(self.ex)  
        
    def testSubset(self):
        km = flow.KMeansOp(name = "KMeans2",
                           channels = ["V2-A", "Y2-A", "B1-A"],
                           scale = {"V2-A" : "logicle",
                                    "Y2-A" : "logicle",
                                    "B1-A" : "logicle"},
                           by = ["Dox"],
                           num_clusters = 20)
        km.estimate(self.ex)
                   
        self.ex = km.apply(self.ex)
        self.ex = flow.ChannelStatisticOp(name = "DoxLen",
                                          channel = "Y2-A",
                                          by = ["KMeans2", "Dox"],
                                          function = len).apply(self.ex)
        self.view.style = "heat"
        self.view.locations = "KMeans2"
        self.view.subset = "Dox == 10.0"
        with self.assertWarns(util.CytoflowViewWarning):
            self.view.plot(self.ex)
        
        
    # Base plot params
    
    def testTitle(self):
        self.ex = flow.ChannelStatisticOp(name = "DoxLen",
                                          channel = "Y2-A",
                                          by = ["KMeans"],
                                          function = len).apply(self.ex)
        self.view.style = "heat"
        self.view.plot(self.ex, title = "Title")
        
    def testLegendLabel(self):
        self.ex = flow.ChannelStatisticOp(name = "DoxLen",
                                          channel = "Y2-A",
                                          by = ["KMeans"],
                                          function = len).apply(self.ex)
        self.view.style = "heat"
        self.view.plot(self.ex, legendlabel = "hue lab")      
        
                                     
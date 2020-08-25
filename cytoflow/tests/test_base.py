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
import matplotlib.pyplot as plt
import numpy as np

import cytoflow as flow


class ClosePlotsWhenDone(object):
    def tearDown(self):
        """Run once after each test"""
        plt.close('all')


class ClosePlotsWhenDoneTest(ClosePlotsWhenDone, unittest.TestCase):
    pass


class ImportedData(ClosePlotsWhenDone):
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
            # thin the dataset 100-fold from 90k to 900 rows for thin=100
            self.ex.add_condition("bucket", "int", np.arange(self.ex.data.shape[0]) % thin)
            self.ex = self.ex.query("bucket == 0")


class ImportedDataTest(ImportedData, unittest.TestCase):
    pass


class ImportedDataSmallTest(ClosePlotsWhenDoneTest):
    def setUp(self):
        """Run once per test at the beginning"""
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/Plate01/"
        tube1 = flow.Tube(file=self.cwd + 'RFP_Well_A3.fcs',
                          conditions={"Dox": 10.0, "Well": "A"})
        tube2 = flow.Tube(file=self.cwd + 'CFP_Well_A4.fcs',
                          conditions={"Dox": 1.0, "Well": "B"})
        import_op = flow.ImportOp(conditions={"Dox": "float", "Well": "category"},
                                  tubes=[tube1, tube2])
        self.ex = import_op.apply()


class TasbeTest(ClosePlotsWhenDoneTest):
    
    def setUp(self):
        """Run once at the beginning of each test"""
        self.cwd = os.path.dirname(os.path.abspath(__file__)) + "/data/tasbe/"
        tube = flow.Tube(file = self.cwd + "rby.fcs")
        self.ex = flow.ImportOp(tubes = [tube])


class View1DTestBase(ImportedData):
    def testPlot(self):
        self.view.plot(self.ex)
        ax = plt.gca()
        assert ax.get_xlabel() == "B1-A"
        np.testing.assert_array_equal(
            ax.get_xticks(),
            np.array([-25000., 0., 25000., 50000., 75000., 100000., 125000.,
                       150000., 175000., 200000.])
        )

    def testLogScale(self):
        self.view.scale = "log"
        self.view.plot(self.ex)
        np.testing.assert_array_equal(
            plt.gca().get_xticks(),
            np.array([1.e-2, 1.e-1, 1., 1.e+1, 1.e+2, 1.e+3, 1.e+4, 1.e+5, 1.e+6, 1.e+7])
        )

    def testLogicleScale(self):
        self.view.scale = "logicle"
        self.view.plot(self.ex)
        np.testing.assert_array_equal(
            plt.gca().get_xticks(),
            np.array([-100., 0., 100., 1000., 10000., 100000.])
        )

    def testXFacet(self, has_colorbar=False):
        self.view.xfacet = "Dox"
        self.view.plot(self.ex)
        check_titles(["Dox = 0.0", "Dox = 10.0", "Dox = 100.0"], has_colorbar)
        assert plt.gcf().get_axes()[2].rowNum == 0  # third subplot is on the first (only) row

    def testYFacet(self, has_colorbar=False):
        self.view.yfacet = "Dox"
        self.view.plot(self.ex)
        check_titles(["Dox = 0.0", "Dox = 10.0", "Dox = 100.0"], has_colorbar)

    def testHueFacet(self):
        self.view.huefacet = "Dox"
        self.view.plot(self.ex)
        assert ['0.0', '10.0', '100.0'] == get_legend_entries(plt.gca())

    def testSubset(self, has_colorbar=False):
        self.view.subset = "Dox == 10.0"
        self.view.xfacet = "Dox"
        self.view.plot(self.ex)
        check_titles(["Dox = 10.0"], has_colorbar)

    # Base plot params

    def testTitle(self):
        self.view.plot(self.ex, title = "Title")
        assert plt.gca().get_title() == "Title"

    def testXlabel(self):
        self.view.plot(self.ex, xlabel = "X lab")
        assert plt.gca().get_xlabel() == "X lab"

    def testYlabel(self):
        self.view.plot(self.ex, ylabel = "Y lab")
        assert plt.gca().get_ylabel() == "Y lab"

    def testHueLabel(self):
        self.view.huefacet = "Well"
        self.view.plot(self.ex, huelabel = "hue lab")
        # TODO assert

    def testColWrap(self):
        self.view.xfacet = "Dox"
        self.view.plot(self.ex, col_wrap = 2)
        assert plt.gcf().get_axes()[2].rowNum == 1  # third subplot is on the second row

    def testShareAxes(self):
        self.view.plot(self.ex, sharex = False, sharey = False)
        # TODO assert

    def testStyle(self):
        self.view.plot(self.ex, sns_style = "darkgrid")
        self.view.plot(self.ex, sns_style = "whitegrid")
        self.view.plot(self.ex, sns_style = "dark")
        self.view.plot(self.ex, sns_style = "white")
        self.view.plot(self.ex, sns_style = "ticks")
        # TODO assert

    def testContext(self):
        self.view.plot(self.ex, sns_context = "paper")
        self.view.plot(self.ex, sns_context = "notebook")
        self.view.plot(self.ex, sns_context = "talk")
        self.view.plot(self.ex, sns_context = "poster")
        # TODO assert

    def testDespine(self):
        self.view.plot(self.ex, despine = False)
        # TODO assert

    # Data plot params

    def testQuantiles(self):
        self.view.plot(self.ex, min_quantile = 0.01, max_quantile = 0.90)
        # TODO assert

    # 1D data plot params

    def testLimits(self):
        self.view.plot(self.ex, lim = (0, 1000))
        assert plt.gca().get_xlim() == (0, 1000)

        self.view.plot(self.ex, lim = (0, 1000), orientation = "horizontal")
        assert plt.gca().get_ylim() == (0, 1000), plt.gca().get_xlim()

    def testOrientation(self):
        self.view.plot(self.ex, orientation = "vertical")  # the default
        ax = plt.gca()
        assert ax.get_xlabel() == "B1-A"
        assert ax.get_ylabel() == ""

        self.view.plot(self.ex, orientation = "horizontal")
        ax = plt.gca()
        assert ax.get_xlabel() == ""
        assert ax.get_ylabel() == "B1-A"


class View2DTestBase(View1DTestBase):
    def testPlot(
        self,
        true_x=(-25000., 0., 25000., 50000., 75000., 100000., 125000., 150000., 175000., 200000.),
        true_y=(-50000., 0., 50000., 100000., 150000., 200000., 250000., 300000.),
    ):
        self.view.plot(self.ex)
        ax = plt.gca()
        assert ax.get_xlabel() == "B1-A"
        assert ax.get_ylabel() == "Y2-A"
        np.testing.assert_array_equal(ax.get_xticks(), np.array(true_x))
        np.testing.assert_array_equal(ax.get_yticks(), np.array(true_y))

    def testLogScale(self):
        self.view.xscale = "log"
        self.view.yscale = "log"
        self.view.plot(self.ex)
        np.testing.assert_array_equal(
            plt.gca().get_xticks(),
            np.array([1.e-2, 1.e-1, 1., 1.e+1, 1.e+2, 1.e+3, 1.e+4, 1.e+5, 1.e+6, 1.e+7])
        )
        np.testing.assert_array_equal(
            plt.gca().get_yticks(),
            np.array([1.e-2, 1.e-1, 1., 1.e+1, 1.e+2, 1.e+3, 1.e+4, 1.e+5, 1.e+6, 1.e+7])
        )

    def testLogicleScale(self):
        self.view.xscale = "logicle"
        self.view.yscale = "logicle"
        self.view.plot(self.ex)
        np.testing.assert_array_equal(
            plt.gca().get_xticks(),
            np.array([-100., 0., 100., 1000., 10000., 100000.])
        )
        np.testing.assert_array_equal(
            plt.gca().get_yticks(),
            np.array([-100., 0., 100., 1000., 10000., 100000.])
        )

    def testOrientation(self):
        pass  # not applicable

    # 2D data plot params
    def testLimits(self):
        self.view.plot(self.ex, xlim = (0, 1000), ylim = (1, 1001))
        assert plt.gca().get_xlim() == (0, 1000)
        assert plt.gca().get_ylim() == (1, 1001)


def get_legend_entries(ax):
    return [t.get_text() for t in ax.get_legend().get_texts()]


def check_titles(correct_titles, has_colorbar=False):
    titles = [ax.get_title() for ax in plt.gcf().get_axes()]
    if has_colorbar:
        correct_titles = correct_titles + [""]
    assert correct_titles == titles, titles

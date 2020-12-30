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
Created on Jan 4, 2018

@author: brian
'''
import unittest, tempfile, os

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.tests.test_base import ImportedDataTest, Base1DViewTest, params_traits_comparator
from cytoflowgui.view_plugins.kde_1d import Kde1DPlugin, Kde1DPlotParams
from cytoflowgui.serialization import save_yaml, load_yaml

class TestKde1D(ImportedDataTest, Base1DViewTest):

    def setUp(self):
        super().setUp()

        self.wi = wi = self.workflow.workflow[-1]
        plugin = Kde1DPlugin()
        self.view = view = plugin.get_view()
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = self.wi
        
        super().setUpView()
                
    def testBaseHistogram(self):
        pass

    def testPlotParams(self):
        super().testPlotParams()
        
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.shade = False
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.alpha = 0.5
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
 
        for k in ['tophat', 'gaussian','epanechnikov','exponential','linear','cosine']:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.kernel = k
            self.workflow.wi_waitfor(self.wi, 'view_error', '')

        for bw in ["silverman", "scott"]:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.bw = bw
            self.workflow.wi_waitfor(self.wi, 'view_error', '')

        for linestyle in ['dashed', 'solid', 'dashdot', 'dotted', 'none']:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.linestyle = linestyle
            self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.gridsize = 50
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

    def testSerialize(self):
        with params_traits_comparator(Kde1DPlotParams):
            fh, filename = tempfile.mkstemp()
            try:
                os.close(fh)

                save_yaml(self.view, filename)
                new_view = load_yaml(filename)
            finally:
                os.unlink(filename)

            self.maxDiff = None

            self.assertDictEqual(self.view.trait_get(self.view.copyable_trait_names()),
                                 new_view.trait_get(self.view.copyable_trait_names()))

    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
        
        exec(code)  # smoke test

        
           
if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestKde1D.testPlotArgs']
    unittest.main()

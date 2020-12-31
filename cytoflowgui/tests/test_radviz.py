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

from cytoflowgui.tests.test_base import ImportedDataTest, BaseDataViewTest, params_traits_comparator
from cytoflowgui.view_plugins.radviz import RadvizPlugin, _Channel, RadvizPlotParams
from cytoflowgui.view_plugins.scatterplot import SCATTERPLOT_MARKERS
from cytoflowgui.serialization import save_yaml, load_yaml

class TestRadviz(ImportedDataTest, BaseDataViewTest):

    def setUp(self):
        super().setUp()

        self.wi = wi = self.workflow.workflow[0]
        self.wi.operation.events = 500
        self.wi.operation.do_estimate = True
        
        plugin = RadvizPlugin()
        self.view = view = plugin.get_view()
        
        view.channels_list = [_Channel(channel = "B1-A", scale = "log"),
                              _Channel(channel = "V2-A", scale = "log"),
                              _Channel(channel = "Y2-A", scale = "log")]

        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = self.wi
        
        super().setUpView()
        
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
                
    def testBase(self):
        pass

    def testChangeScale(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.channels_list[1].scale = "linear"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

    def testChangeChannel(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.channels_list[1].channel = "FSC-A"
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testAddChannel(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.channels_list.append(_Channel(channel = "FSC-A", scale = "log"))
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

    def testRemoveChannel(self):
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.channels_list.append(_Channel(channel = "FSC-A", scale = "log"))
        self.workflow.wi_waitfor(self.wi, 'view_error', '')

        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.channels_list.pop()
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
        
    def testPlotParams(self):
 
        super().testPlotParams()
 
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.alpha = 0.5
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
 
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.s = 5
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
                                    
        self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
        self.view.plot_params.marker = '+'
        self.workflow.wi_waitfor(self.wi, 'view_error', '')
                                    
        for m in SCATTERPLOT_MARKERS[::-1]:
            self.workflow.wi_sync(self.wi, 'view_error', 'waiting')
            self.view.plot_params.marker = m
            self.workflow.wi_waitfor(self.wi, 'view_error', '')
    
    def testNotebook(self):
        # smoke test
        
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
            
            for view in wi.views:
                code = code + view.get_notebook_code(i)
         
        exec(code)

    def testSerialize(self):
        with params_traits_comparator(_Channel), params_traits_comparator(RadvizPlotParams):
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


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestRadviz.testBase']
    unittest.main()

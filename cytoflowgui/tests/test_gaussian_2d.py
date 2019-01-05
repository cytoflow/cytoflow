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
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.tests.test_base import ImportedDataTest, wait_for
from cytoflowgui.op_plugins import GaussianMixture2DPlugin
from cytoflowgui.subset import CategorySubset
from cytoflowgui.view_plugins.scatterplot import SCATTERPLOT_MARKERS
from cytoflowgui.serialization import load_yaml, save_yaml

class TestGaussian2D(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = GaussianMixture2DPlugin()
        self.op = op = plugin.get_operation()
        
        op.name = "Gauss"
        op.xchannel = "V2-A"
        op.ychannel = "Y2-A"
        op.xscale = "logicle"
        op.yscale = "logicle"
        op.num_components = 2
        
        op.subset_list.append(CategorySubset(name = "Well", values = ["A", "B"]))
        
        self.wi = wi = WorkflowItem(operation = op)
        wi.default_view = op.default_view()
        wi.view_error = "Not yet plotted"
        wi.views.append(self.wi.default_view)
        
        self.workflow.workflow.append(wi)
        self.workflow.selected = wi
        
        # run estimate
        op.do_estimate = True
        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 30))

    def testEstimate(self):
        self.assertIsNotNone(self.workflow.remote_eval("self.workflow[-1].result"))
   
    def testChangeChannels(self):
        self.op.xchannel = "B1-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.op.ychannel = "V2-A"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        

    def testChangeScale(self):
        self.op.xscale = "log"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

        self.op.yscale = "log"
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
    def testChangeBy(self):
        self.op.by = ["Dox"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
    def testChangeComponents(self):
        self.op.num_components = 3
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))

    def testChangeSigma(self):
        self.op.sigma = 1
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))

        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))      
         
   
    def testChangeSubset(self):
        self.op.subset_list[0].selected = ["A"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
          
          
    def testPlot(self):
        self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        
    def testPlotFacets(self):
        self.op.by = ["Dox", "Well"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.view = self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = "Dox"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.yfacet = ""
        self.view.huefacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
        
        
    def testPlotArgs(self):
        self.op.by = ["Dox", "Well"]
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v != 'valid', 30))
        self.assertTrue(self.workflow.remote_eval("self.workflow[-1].result is None"))
         
        self.op.do_estimate = True
        self.assertTrue(wait_for(self.wi, 'status', lambda v: v == 'valid', 30))
        
        self.view = self.wi.current_view = self.wi.default_view
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        # Common params
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = "Dox"
        self.view.yfacet = "Well"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.title = "Title"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.xlabel = "X label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.ylabel = "Y label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.sharex = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.sharey = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.despine = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.xfacet = ""
        self.view.huefacet = "Dox"
        self.view.plot_params.huelabel = "Hue label"
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.legend = False
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        ## Scatterplot-specific params
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.min_quantile = 0.01
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.max_quantile = 0.90
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.alpha = 0.5
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))

        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
        self.view.plot_params.s = 5
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
                                    
        for m in SCATTERPLOT_MARKERS:
            self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 30))
            self.view.plot_params.marker = m
            self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 30))
                        
   
 
    def testSerialize(self):
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
             
            save_yaml(self.op, filename)
            new_op = load_yaml(filename)
             
        finally:
            os.unlink(filename)
             
        self.maxDiff = None
                      
        self.assertDictEqual(self.op.trait_get(self.op.copyable_trait_names()),
                             new_op.trait_get(self.op.copyable_trait_names()))
         
         
    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
         
        exec(code)
        nb_data = locals()['ex_1'].data
        remote_data = self.workflow.remote_eval("self.workflow[-1].result.data")
        self.assertTrue((nb_data == remote_data).all().all())

if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestGaussian2D.testPlotArgs']
    unittest.main()
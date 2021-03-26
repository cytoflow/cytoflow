#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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

import os, tempfile, pandas

from cytoflowgui.tests.test_base import ImportedDataTest, params_traits_comparator
from cytoflowgui.serialization import load_yaml, save_yaml, save_notebook
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.subset import CategorySubset, RangeSubset
from cytoflowgui.op_plugins.import_op import ImportPluginOp
from cytoflowgui.op_plugins.channel_stat import ChannelStatisticPlugin, ChannelStatisticPluginOp

class TestWorkflowItem(ImportedDataTest):
    
    def setUp(self):
        super().setUp()
        
        stats_plugin = ChannelStatisticPlugin()

        stats_op = stats_plugin.get_operation()
        stats_op.name = "MeanByDoxWell"
        stats_op.channel = "Y2-A"
        stats_op.statistic_name = "Geom.Mean"
        stats_op.by = ['Dox', 'Well']
        stats_op.subset_list.append(CategorySubset(name = "Well",
                                                   values = ['A', 'B']))
        stats_op.subset_list.append(RangeSubset(name = "Dox",
                                                values = [1.0, 10.0, 100.0]))
        stats_op.subset_list.append(RangeSubset(name = "IP",
                                                values = [1.0, 10.0]))

        stats_wi = WorkflowItem(operation = stats_op,
                                  status = "waiting",
                                  view_error = "Not yet plotted")
        self.workflow.workflow.append(stats_wi)
        self.workflow.wi_waitfor(stats_wi, 'status', 'valid')

        self.wi = wi = self.workflow.workflow[-1]
        self.op = self.wi.operation
        self.workflow.selected = wi
                
    def testSerializeMultiIndexV1(self):
        with params_traits_comparator(WorkflowItem, ImportPluginOp, ChannelStatisticPluginOp):
            fh, filename = tempfile.mkstemp()
            try:
                os.close(fh)
                 
                save_yaml(self.workflow.workflow, filename, lock_versions = {pandas.MultiIndex : 1})
                new_workflow = load_yaml(filename)
                 
            finally:
                os.unlink(filename)
                 
            self.maxDiff = None

            for i in range(len(new_workflow)):
                self.assertDictEqual(self.workflow.workflow[i].trait_get(self.workflow.workflow[i].copyable_trait_names(status = lambda t: t is not True)),
                                     new_workflow[i].trait_get(self.workflow.workflow[i].copyable_trait_names(status = lambda t: t is not True)))

        
        
    def testSerialize(self):
        with params_traits_comparator(WorkflowItem, ImportPluginOp, ChannelStatisticPluginOp):
            fh, filename = tempfile.mkstemp()
            try:
                os.close(fh)
                 
                save_yaml(self.workflow.workflow, filename)
                new_workflow = load_yaml(filename)
                 
            finally:
                os.unlink(filename)
                 
            self.maxDiff = None

            for i in range(len(new_workflow)):
                self.assertDictEqual(self.workflow.workflow[i].trait_get(self.workflow.workflow[i].copyable_trait_names(status = lambda t: t is not True)),
                                     new_workflow[i].trait_get(self.workflow.workflow[i].copyable_trait_names(status = lambda t: t is not True)))
             
             
    def testSaveNotebook(self):
        # this is just a smoke test
        
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
            
            save_notebook(self.workflow.workflow, filename)
            
        finally:
            os.unlink(filename)
            

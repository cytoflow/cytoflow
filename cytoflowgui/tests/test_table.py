'''
Created on Jan 5, 2018

@author: brian
'''

import os, unittest, tempfile

import matplotlib
import pandas as pd
matplotlib.use("Agg")

from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.op_plugins import ChannelStatisticPlugin
from cytoflowgui.view_plugins.table import TablePlugin
from cytoflowgui.serialization import load_yaml, save_yaml, traits_eq, traits_hash
from cytoflowgui.view_plugins.i_view_plugin import EmptyPlotParams

from test_base import ImportedDataTest, wait_for  # @UnresolvedImport

class TestTable(ImportedDataTest):
    
    def setUp(self):
        ImportedDataTest.setUp(self)

        plugin = ChannelStatisticPlugin()
        
        op = plugin.get_operation()
        op.name = "MeanByDox"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.SD"
        op.by = ['Dox']

        wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        
        op = plugin.get_operation()
        op.name = "MeanByDoxAndWell"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.SD"
        op.by = ['Dox', 'Well']

        wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        
        op = plugin.get_operation()
        op.name = "MeanByDox"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.Mean"
        op.by = ['Dox']
                
        self.wi = wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        
        op = plugin.get_operation()
        op.name = "MeanByDoxAndWell"
        op.channel = "Y2-A"
        op.statistic_name = "Geom.Mean"
        op.by = ['Dox', 'Well']
                
        self.wi = wi = WorkflowItem(operation = op)        
        self.workflow.workflow.append(wi)
        
        self.workflow.selected = wi

        self.assertTrue(wait_for(wi, 'status', lambda v: v == 'valid', 10))
        
        plugin = TablePlugin()
        self.view = view = plugin.get_view()
        view.statistic = ("MeanByDox", "Geom.Mean")
        view.row_facet = "Dox"
        
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
  
        wi.views.append(view)
        wi.current_view = view
        self.workflow.selected = wi
        
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
    def tearDown(self):
        fh, filename = tempfile.mkstemp()
        
        try:
            os.close(fh)
            
            data = pd.DataFrame(index = self.view.result.index)
            data[self.view.result.name] = self.view.result   
        
            self.view._export_data(data, self.view.result.name, filename)
        finally:
            os.unlink(filename)


    def testRow(self):
        pass
    
    def testColumn(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
   
        self.view.row_facet = ""
        self.view.column_facet = "Dox"
           
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
    def testSubRow(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
   
        self.view.statistic = ("MeanByDoxAndWell", "Geom.Mean")
        self.view.row_facet = "Dox"
        self.view.subrow_facet = "Well"
           
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))    
        
    def testSubColumn(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
   
        self.view.statistic = ("MeanByDoxAndWell", "Geom.Mean")
        self.view.row_facet = ""
        self.view.column_facet = "Dox"
        self.view.subcolumn_facet = "Well"
           
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
    def testRowRange(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
   
        self.view.statistic = ("MeanByDox", "Geom.SD")
           
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
    
    def testColumnRange(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
   
        self.view.statistic = ("MeanByDox", "Geom.SD")
        self.view.row_facet = ""
        self.view.column_facet = "Dox"
           
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))
        
    def testSubRowRange(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
   
        self.view.statistic = ("MeanByDoxAndWell", "Geom.SD")
        self.view.row_facet = "Dox"
        self.view.subrow_facet = "Well"
           
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))    
        
    def testSubColumnRange(self):
        self.workflow.remote_exec("self.workflow[-1].view_error = 'waiting'")
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "waiting", 5))
   
        self.view.statistic = ("MeanByDoxAndWell", "Geom.SD")
        self.view.row_facet = ""
        self.view.column_facet = "Dox"
        self.view.subcolumn_facet = "Well"
           
        self.assertTrue(wait_for(self.wi, 'view_error', lambda v: v == "", 5))

 
    def testSerialize(self):
        
        EmptyPlotParams.__eq__ = traits_eq
        EmptyPlotParams.__hash__ = traits_hash
        
        fh, filename = tempfile.mkstemp()
        try:
            os.close(fh)
               
            save_yaml(self.view, filename)
            new_view = load_yaml(filename)
               
        finally:
            os.unlink(filename)
               
        self.maxDiff = None
        
        old_traits = self.view.trait_get(self.view.copyable_trait_names())
        new_traits = new_view.trait_get(self.view.copyable_trait_names())
        
        # we don't serialize the result
        old_traits['result'] = None
                        
        self.assertDictEqual(old_traits, new_traits)
           
           
    def testNotebook(self):
        code = "from cytoflow import *\n"
        for i, wi in enumerate(self.workflow.workflow):
            code = code + wi.operation.get_notebook_code(i)
           
        exec(code) # smoke test


if __name__ == "__main__":
#     import sys;sys.argv = ['', 'TestTable.testColumn']
    unittest.main()
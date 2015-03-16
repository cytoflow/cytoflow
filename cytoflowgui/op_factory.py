"""
Created on Mar 15, 2015

@author: brian
"""
from envisage.api import Plugin, ExtensionPoint
from traits.api import List
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin

class OperationFactory(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflow.op_factory'
    name = "Operation Factory"
    
    plugins = ExtensionPoint(List(IOperationPlugin), 
                             id = "edu.mit.synbio.cytoflow.op_plugins")
    
    def count(self):
        print len(self.plugins)
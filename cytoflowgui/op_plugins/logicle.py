"""
Created on Feb 24, 2015

@author: brian
"""
from traits.api import provides, Callable
from traitsui.api import Controller, View, Item, CheckListEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import LogicleTransformOp
from cytoflowgui.op_plugins import OpHandlerMixin, IOperationPlugin, OP_PLUGIN_EXT

class LogicleHandler(Controller, OpHandlerMixin):
    """
    classdocs
    """
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.T'),
                    Item('object.W'),
                    Item('object.M'),
                    Item('object.A'),
                    Item('object.r'),
                    Item('object.channels',
                         editor = CheckListEditor(name='handler.previous_channels',
                                                  cols = 2),
                         style = 'custom'))
        
        
    # TODO - how to indicate an exception? like "no data <0" for the estimate?
    
@provides(IOperationPlugin)
class LogiclePlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.logicle'
    operation_id = 'edu.mit.synbio.cytoflow.operations.logicle'
    
    short_name = "Logicle"
    menu_group = "Transformations"
     
    def get_operation(self):
        ret = LogicleTransformOp()
        ret.add_trait("handler_factory", Callable)
        ret.handler_factory = LogicleHandler
        return ret
    
    def get_default_view(self, op):
        return None
    
    def get_icon(self):
        return ImageResource('logicle')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

    
        
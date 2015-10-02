"""
Created on Feb 24, 2015

@author: brian
"""
from traits.api import provides, Callable
from traitsui.api import Controller, View, Item, CheckListEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import HlogTransformOp
from cytoflowgui.op_plugins.i_op_plugin \
    import OpHandlerMixin, IOperationPlugin, OP_PLUGIN_EXT, PluginOpMixin

class HLogHandler(Controller, OpHandlerMixin):
    """
    classdocs
    """
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channels',
                         editor = CheckListEditor(name='handler.previous_channels',
                                                  cols = 2),
                         style = 'custom'))
        
class HLogTransformPluginOp(HlogTransformOp, PluginOpMixin):
    handler_factory = Callable(HLogHandler)
    
@provides(IOperationPlugin)
class HLogPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.hlog'
    operation_id = 'edu.mit.synbio.cytoflow.operations.hlog'
    
    short_name = "Hyperlog"
    menu_group = "Transformations"
     
    def get_operation(self):
        return HLogTransformPluginOp()
    
    def get_default_view(self, op):
        return None
    
    def get_icon(self):
        return ImageResource('hlog')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

    
        
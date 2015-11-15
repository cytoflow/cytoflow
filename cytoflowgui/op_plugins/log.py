"""
Created on Feb 24, 2015

@author: brian
"""
from traits.api import provides, Callable
from traitsui.api import Controller, View, Item, CheckListEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import LogTransformOp
from cytoflowgui.op_plugins.i_op_plugin \
    import OpHandlerMixin, IOperationPlugin, OP_PLUGIN_EXT, PluginOpMixin
from cytoflowgui.color_text_editor import ColorTextEditor

class LogHandler(Controller, OpHandlerMixin):
    """
    classdocs
    """
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channels',
                         editor = CheckListEditor(name='handler.previous_channels',
                                                  cols = 2),
                         style = 'custom'),
                    Item('handler.wi.error',
                         label = 'Error',
                         visible_when = 'handler.wi.error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191",
                                                  word_wrap = True)))
        
class LogTransformPluginOp(LogTransformOp, PluginOpMixin):
    handler_factory = Callable(LogHandler)
    
@provides(IOperationPlugin)
class LogPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.log'
    operation_id = 'edu.mit.synbio.cytoflow.operations.log'
    
    short_name = "Log"
    menu_group = "Transformations"
     
    def get_operation(self):
        return LogTransformPluginOp()
    
    def get_default_view(self):
        return None
    
    def get_icon(self):
        return ImageResource('log')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

    
        
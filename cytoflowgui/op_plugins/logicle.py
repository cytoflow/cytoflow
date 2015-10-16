"""
Created on Feb 24, 2015

@author: brian
"""
from traits.api import provides, Callable, on_trait_change
from traitsui.api import Controller, View, Item, CheckListEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import LogicleTransformOp
from cytoflowgui.op_plugins.i_op_plugin \
    import OpHandlerMixin, IOperationPlugin, OP_PLUGIN_EXT, PluginOpMixin
from cytoflowgui.color_text_editor import ColorTextEditor

class LogicleHandler(Controller, OpHandlerMixin):
    """
    classdocs
    """
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.W'),
                    Item('object.M'),
                    Item('object.A'),
                    Item('object.r'),
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
        
    def setattr(self, info, obj, name, value):
        super(LogicleHandler, self).setattr(info, obj, name, value)
        #Controller.setattr(self, info, object, name, value)
        
class LogicleTransformPluginOp(LogicleTransformOp, PluginOpMixin):
    handler_factory = Callable(LogicleHandler)
    
    @on_trait_change('channels[]')
    def _on_channels_changed(self):
        for channel in self.channels:
            if channel not in self.W:
                self.W[channel] = 0.5
            if channel not in self.A:
                self.A[channel] = 0.0
    
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
        return LogicleTransformPluginOp()
    
    def get_default_view(self):
        return None
    
    def get_icon(self):
        return ImageResource('logicle')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

    
        
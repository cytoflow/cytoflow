'''
Created on Oct 9, 2015

@author: brian
'''

from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow.operations.binning import BinningOp
from pyface.api import ImageResource
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflow.views.i_selectionview import ISelectionView
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.color_text_editor import ColorTextEditor


class BinningHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Channel"),
                    Item('object.scale'),
                    Item('object.bin_width'),
                    Item('handler.wi.error',
                         label = 'Error',
                         visible_when = 'handler.wi.error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191",
                                                  word_wrap = True))) 

class BinningPluginOp(BinningOp, PluginOpMixin):
    handler_factory = Callable(BinningHandler)

@provides(IOperationPlugin)
class BinningPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.binning'
    operation_id = 'edu.mit.synbio.cytoflow.operations.binning'

    short_name = "Range"
    menu_group = "Gates"
    
    def get_operation(self):
        return BinningPluginOp()
    
    def get_default_view(self):
        return None
    
    def get_icon(self):
        return ImageResource('binning')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
'''
Created on Oct 9, 2015

@author: brian
'''

from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow.operations.binning import BinningOp, BinningView
from pyface.api import ImageResource
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflow.views.i_selectionview import IView
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.color_text_editor import ColorTextEditor

class BinningHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Channel"),
                    Item('object.scale'),
                    Item('object.num_bins', label = "Num Bins"),
                    Item('object.bin_width'),
                    Item('handler.wi.error',
                         label = 'Error',
                         visible_when = 'handler.wi.error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191",
                                                  word_wrap = True))) 

class BinningPluginOp(BinningOp, PluginOpMixin):
    handler_factory = Callable(BinningHandler)


class BinningViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('object.name',
                         style = 'readonly'),
                    Item('object.channel',
                         style = 'readonly'),
                    Item('object.huefacet',
                         style = 'readonly'),
                    Item('_'),
                    Item('object.subset',
                         label = "Subset",
                         editor = SubsetEditor(experiment = 'handler.wi.previous.result')))

@provides(IView)
class BinningPluginView(BinningView, PluginViewMixin):
    handler_factory = Callable(BinningViewHandler)

@provides(IOperationPlugin)
class BinningPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.binning'
    operation_id = 'edu.mit.synbio.cytoflow.operations.binning'

    short_name = "Binning"
    menu_group = "Gates"
    
    def get_operation(self):
        return BinningPluginOp()
    
    def get_default_view(self):
        return BinningPluginView()
    
    def get_icon(self):
        return ImageResource('binning')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
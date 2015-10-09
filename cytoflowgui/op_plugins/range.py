from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow.operations.range import RangeOp, RangeSelection
from pyface.api import ImageResource
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflow.views.i_selectionview import ISelectionView
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.color_text_editor import ColorTextEditor


class RangeHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Channel"),
                    Item('object.low'),
                    Item('object.high'),
                    Item('handler.wi.error',
                         label = 'Error',
                         visible_when = 'handler.wi.error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191",
                                                  word_wrap = True))) 
        
class RangeViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('object.name',
                         style = "readonly"),
                    Item('object.channel', 
                         label = "Channel",
                         style = "readonly"),
                    Item('_'),
                    Item('object.subset',
                         label = "Subset",
                         editor = SubsetEditor(experiment = 'handler.wi.previous.result')))

@provides(ISelectionView)
class RangeSelectionView(RangeSelection, PluginViewMixin):
    handler_factory = Callable(RangeViewHandler)
    
class RangePluginOp(RangeOp, PluginOpMixin):
    handler_factory = Callable(RangeHandler)

@provides(IOperationPlugin)
class RangePlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.range'
    operation_id = 'edu.mit.synbio.cytoflow.operations.range'

    short_name = "Range"
    menu_group = "Gates"
    
    def get_operation(self):
        return RangePluginOp()
    
    def get_default_view(self):
        return RangeSelectionView()
    
    def get_icon(self):
        return ImageResource('range')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
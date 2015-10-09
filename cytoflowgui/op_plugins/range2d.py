'''
Created on Apr 25, 2015

@author: brian
'''

from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable
from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, PluginOpMixin, OP_PLUGIN_EXT
from cytoflow.operations.range2d import Range2DOp, RangeSelection2D
from pyface.api import ImageResource
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflow.views.i_selectionview import ISelectionView
from cytoflowgui.color_text_editor import ColorTextEditor

class Range2DHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.xchannel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "X Channel"),
                    Item('object.xlow', label = "X Low"),
                    Item('object.xhigh', label = "X High"),
                    Item('object.ychannel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Y Channel"),
                    Item('object.ylow', label = "Y Low"),
                    Item('object.yhigh', label = "Y High"),
                    Item('handler.wi.error',
                         label = 'Error',
                         visible_when = 'handler.wi.error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191",
                                                  word_wrap = True))) 
        
class RangeView2DHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('object.name', 
                         style = 'readonly'),
                    Item('object.xchannel', 
                         label = "X Channel", 
                         style = 'readonly'),
                    Item('object.ychannel',
                         label = "Y Channel",
                         style = 'readonly'),
                    Item('_'),
                    Item('object.subset',
                         label = "Subset",
                         editor = SubsetEditor(experiment = 'handler.wi.previous.result')))

@provides(ISelectionView)
class Range2DSelectionView(RangeSelection2D, PluginViewMixin):
    handler_factory = Callable(RangeView2DHandler)
    
class Range2DPluginOp(Range2DOp, PluginOpMixin):
    handler_factory = Callable(Range2DHandler)

@provides(IOperationPlugin)
class Range2DPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.range2d'
    operation_id = 'edu.mit.synbio.cytoflow.operations.range2d'

    short_name = "Range 2D"
    menu_group = "Gates"
    
    def get_operation(self):
        return Range2DPluginOp()
    
    def get_default_view(self):
        return Range2DSelectionView()

    def get_icon(self):
        return ImageResource('range2d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
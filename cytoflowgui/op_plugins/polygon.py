'''
Created on Apr 25, 2015

@author: brian
'''

from traitsui.api import View, Item, EnumEditor, Controller, Handler
from envisage.api import Plugin, contributes_to
from traits.api import provides, DelegatesTo, Callable, Instance, Callable
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow import PolygonOp, ScatterplotView, PolygonSelection
from pyface.api import ImageResource
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflow.views.i_selectionview import ISelectionView
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.color_text_editor import ColorTextEditor

class PolygonHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.xchannel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "X Channel"),
                    Item('object.ychannel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Y Channel"),
                    Item('object.vertices', label = "Vertices"),
                    Item('handler.wi.error',
                         label = 'Error',
                         visible_when = 'handler.wi.error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191",
                                                  word_wrap = True))) 
        
class PolygonViewHandler(Controller, ViewHandlerMixin):
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
class PolygonSelectionView(PolygonSelection, PluginViewMixin):
    handler_factory = Callable(PolygonViewHandler)
    
    view = Instance(ScatterplotView, args = ())
    name = DelegatesTo('view')
    xchannel = DelegatesTo('view')
    ychannel = DelegatesTo('view')
    subset = DelegatesTo('view')
    
class PolygonPluginOp(PolygonOp, PluginOpMixin):
    handler_factory = Callable(PolygonHandler)

@provides(IOperationPlugin)
class PolygonPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.polygon'
    operation_id = 'edu.mit.synbio.cytoflow.operations.polygon'

    short_name = "Polygon Gate"
    menu_group = "Gates"
    
    def get_operation(self):
        return PolygonPluginOp()
    
    def get_default_view(self, op):
        view = PolygonSelectionView()
         
        # we have to make these traits on the top-level selection view
        # so that the change handlers get updated.
         
        op.sync_trait('xchannel', view, mutual = True)
        op.sync_trait('ychannel', view, mutual = True)
        op.sync_trait('name', view, mutual = True)
        op.sync_trait('vertices', view, mutual = True)
         
        return view
     
    def get_icon(self):
        return ImageResource('polygon')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
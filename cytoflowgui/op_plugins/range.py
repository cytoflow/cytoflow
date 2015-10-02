from traitsui.api import View, Item, EnumEditor, Controller, Handler
from envisage.api import Plugin, contributes_to
from traits.api import provides, DelegatesTo, Callable, Instance
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow import RangeOp, RangeSelection, HistogramView
from pyface.api import ImageResource
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflow.views.i_selectionview import ISelectionView


class RangeHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Channel"),
                    Item('object.low'),
                    Item('object.high')) 
        
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
class RangeSelectionView(RangeSelection):
    handler = Instance(Handler, transient = True)
    handler_factory = Callable(RangeViewHandler)
    
    view = Instance(HistogramView, args = ())
    name = DelegatesTo('view')
    channel = DelegatesTo('view')
    subset = DelegatesTo('view')

    def plot_wi(self, wi, pane):
        pane.plot(wi.previous.result, self) 

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
        ret = RangeOp()
        ret.add_trait("handler_factory", Callable)
        ret.handler_factory = RangeHandler
        return ret
    
    def get_default_view(self, op):
        view = RangeSelectionView()
        
        # we have to make these traits on the top-level ThresholdSelection
        # so that the change handlers get updated.
        
        op.sync_trait('channel', view, mutual = True)
        op.sync_trait('name', view, mutual = True)
        op.sync_trait('low', view, mutual = True)
        op.sync_trait('high', view, mutual = True)
        
        return view
    
    def get_icon(self):
        return ImageResource('range')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
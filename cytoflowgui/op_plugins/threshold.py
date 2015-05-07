from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from traits.api import provides, DelegatesTo, Callable
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow import ThresholdOp
from pyface.api import ImageResource
from cytoflow.views.threshold_selection import ThresholdSelection
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflow.views.histogram import HistogramView


class ThresholdHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor=EnumEditor(name='handler.wi.previous.channels'),
                         label = "Channel"),
                    Item('object.threshold')) 
        
class ThresholdViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(Item('object.name',
                         style = "readonly"),
                    Item('object.channel', 
                         label = "Channel",
                         style = "readonly"),
                    Item('_'),
                    Item('object.subset',
                         label = "Subset",
                         editor = SubsetEditor(experiment = 'handler.wi.result')))

class ThresholdSelectionView(ThresholdSelection):
    handler_factory = Callable(ThresholdViewHandler)
    
    def __init__(self, **kwargs):
        super(ThresholdSelectionView, self).__init__(**kwargs)
        
        self.view = HistogramView()
        
        self.add_trait('name', DelegatesTo('view'))
        self.add_trait('channel', DelegatesTo('view'))
        self.add_trait('subset', DelegatesTo('view'))
        
    def is_wi_valid(self, wi):
        return (wi.previous 
                and wi.previous.result 
                and self.is_valid(wi.previous.result))
    
    def plot_wi(self, wi, pane):
        pane.plot(wi.previous.result, self) 

@provides(IOperationPlugin)
class ThresholdPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op.threshold'
    operation_id = 'edu.mit.synbio.cytoflow.op.threshold'

    short_name = "Threshold"
    menu_group = "Gates"
    
    def get_operation(self):
        ret = ThresholdOp()
        ret.handler_factory = ThresholdHandler
        return ret
    
    def get_default_view(self, op):
        view = ThresholdSelectionView()
        
        # we have to make these traits on the top-level ThresholdSelection
        # so that the change handlers get updated.
        
        op.sync_trait('channel', view, mutual = True)
        op.sync_trait('name', view, mutual = True)
        op.sync_trait('threshold', view, mutual = True)
        
        return view
    
    def get_icon(self):
        return ImageResource('threshold')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
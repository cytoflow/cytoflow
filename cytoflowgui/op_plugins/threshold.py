from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from traits.api import provides, Instance, DelegatesTo
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow import ThresholdOp
from cytoflow.operations.i_operation import IOperation
from pyface.api import ImageResource
from cytoflow.views.threshold_selection import ThresholdSelection
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflow.views.histogram import HistogramView
#from pyface.qt import QtGui
#import cytoflowgui.resources

class ThresholdHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor=EnumEditor(name='handler.previous_channels'),
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
        view = ThresholdSelection(view = HistogramView())
        
        # we have to make these traits on the top-level ThresholdSelection
        # so that the change handlers get updated.
        
        view.add_trait('name', DelegatesTo('view'))
        view.add_trait('channel', DelegatesTo('view'))
        view.add_trait('subset', DelegatesTo('view'))
        
        op.sync_trait('channel', view, mutual = True)
        op.sync_trait('name', view, mutual = True)
        op.sync_trait('threshold', view, mutual = True)
        
        view.handler_factory = ThresholdViewHandler 
        return view
    
    def get_icon(self):
        return ImageResource('threshold')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
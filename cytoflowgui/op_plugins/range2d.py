'''
Created on Apr 25, 2015

@author: brian
'''

from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from traits.api import provides, DelegatesTo, Callable
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow import Range2DOp
from pyface.api import ImageResource
from cytoflow.views.threshold_selection import ThresholdSelection
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin
from cytoflowgui.subset_editor import SubsetEditor
from cytoflow.views.histogram import HistogramView

class Range2DHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.xchannel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Channel"),
                    Item('object.xlow'),
                    Item('object.xhigh'),
                    Item('object.ychannel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Channel"),
                    Item('object.ylow'),
                    Item('object.yhigh')) 

@provides(IOperationPlugin)
class Range2DPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.operations.range2d'
    operation_id = 'edu.mit.synbio.cytoflow.operations.range2d'

    short_name = "Range 2D"
    menu_group = "Gates"
    
    def get_operation(self):
        ret = Range2DOp()
        ret.handler_factory = Range2DHandler
        return ret
    
    def get_default_view(self, op):
        return None
#         view = ThresholdSelectionView()
#         
#         # we have to make these traits on the top-level ThresholdSelection
#         # so that the change handlers get updated.
#         
#         op.sync_trait('channel', view, mutual = True)
#         op.sync_trait('name', view, mutual = True)
#         op.sync_trait('threshold', view, mutual = True)
#         
#         return view
#     
    def get_icon(self):
        return ImageResource('range2d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
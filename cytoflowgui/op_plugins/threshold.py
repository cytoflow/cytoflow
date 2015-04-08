from traitsui.api import View, Item, EnumEditor, Controller
from envisage.api import Plugin, contributes_to
from traits.api import provides
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT
from cytoflow import ThresholdOp
from cytoflow.operations.i_operation import IOperation
from pyface.api import ImageResource
#from pyface.qt import QtGui
#import cytoflowgui.resources

@provides(IOperation)
class ThresholdHandler(Controller, OpHandlerMixin):
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor=EnumEditor(name='handler.previous_channels'),
                         label = "Channel"),
                    Item('object.threshold')) 

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
    
    def get_icon(self):
        return ImageResource('threshold')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
from traitsui.api import View, Item, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin,\
    OpWrapperMixin, OP_PLUGIN_EXT
from cytoflow import ThresholdOp
from cytoflow.operations.i_operation import IOperation
from pyface.qt import QtGui

@provides(IOperation)
class ThresholdOpWrapper(ThresholdOp, OpWrapperMixin):
    
    def default_traits_view(self):
        return View(Item('name'),
            Item('channel',
                 editor=EnumEditor(name='previous_channels'),
                 label = "Channel"),
            Item('threshold')) 

@provides(IOperationPlugin)
class ThresholdPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op.threshold'
    operation_id = 'edu.mit.synbio.cytoflow.op.threshold'

    short_name = "Threshold"
    menu_group = "Gates"
    
    def get_operation(self, wi):
        return ThresholdOpWrapper(wi = wi)
    
    def get_icon(self):
        return QtGui.QIcon()
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
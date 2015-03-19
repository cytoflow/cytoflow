from traitsui.api import ModelView, View, Item
from traits.api import Bool
from envisage.api import Plugin, contributes_to
from traits.api import provides, Property
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin,\
    MOperationPlugin
from cytoflow import ThresholdOp
from pyface.qt import QtGui

class ThresholdHandler(ModelView):
    """
    class docs
    """
    b = Bool
    
    traits_view = View(Item(name='b'))

@provides(IOperationPlugin)
class ThresholdPlugin(Plugin, MOperationPlugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflow.op.threshold' 
    name = "Threshold Operation"
    short_name = "Threshold"
    menu_group = "Gates"
    
    def get_operation(self):
        return ThresholdOp()
    
    def get_handler(self):
        return ThresholdHandler()
    
    def get_icon(self):
        return QtGui.QIcon()
    
    @contributes_to('edu.mit.synbio.cytoflow.op_plugins')
    def get_plugin(self):
        return self
    
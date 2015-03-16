from traitsui.api import ModelView

from envisage.api import Plugin, contributes_to
from traits.api import provides
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin
from cytoflow import ThresholdOp
from pyface.qt import QtGui

class ThresholdHandler(ModelView):
    """
    class docs
    """
    pass

@provides(IOperationPlugin)
class ThresholdPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflow.op.threshold' 
    name = "Threshold Operation"
    
    def get_operation(self):
        return ThresholdOp()
    
    def get_handler(self):
        return ThresholdHandler()
    
    def get_icon(self):
        return QtGui.QIcon()
    
    @contributes_to('edu.mit.synbio.cytoflow.op_plugins')
    def get_plugin(self):
        return self
    
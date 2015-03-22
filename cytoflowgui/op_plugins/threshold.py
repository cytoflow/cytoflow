from traitsui.api import View, Item, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides
from cytoflowgui.op_plugins.i_op_plugin import IOperationPlugin,\
    MOperationPlugin, OP_PLUGIN_EXT
from cytoflow import ThresholdOp
from pyface.qt import QtGui

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
    
    def get_traitsui_view(self, model):
        return View(Item('object.operation.name'),
                    Item('object.operation.channel',
                         editor=EnumEditor(name='previous_channels'),
                         label = "Channel"),
                    Item('object.operation.threshold'))
        
    
    def get_icon(self):
        return QtGui.QIcon()
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
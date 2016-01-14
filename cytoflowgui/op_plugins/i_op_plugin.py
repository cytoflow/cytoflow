"""
Created on Mar 15, 2015

@author: brian
"""
from traits.api import Interface, Str, HasTraits, Instance, Property, List
from traitsui.api import Handler
from cytoflowgui.workflow_item import WorkflowItem

OP_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.op_plugins'

class IOperationPlugin(Interface):
    """
    Attributes
    ----------
    
    id : Str
        The Envisage ID used to refer to this plugin
        
    operation_id : Str
        Same as the "id" attribute of the IOperation this plugin wraps.
        
    short_name : Str
        The operation's "short" name - for menus and toolbar tool tips
        
    menu_group : Str
        If we were to put this op in a menu, what submenu to use?
        Not currently used.
    """
    
    operation_id = Str
    short_name = Str
    menu_group = Str

    def get_operation(self):
        """
        Return an instance of the IOperation that this plugin wraps, along
        with the factory for the handler
        """
        
        
    def get_default_view(self):
        """
        Return an IView instance set up to be the default view for the operation.
        """

    def get_icon(self):
        """
        
        """

class PluginOpMixin(HasTraits):
    error = Str(transient = True)
        
class OpHandlerMixin(HasTraits):
    wi = Instance(WorkflowItem)
    
    previous_channels = Property(List, depends_on = 'wi.previous.metadata')
    previous_conditions = Property(List, depends_on = 'wi.previous.conditions')

    # MAGIC: provides dynamically updated values for the "channels" trait
    def _get_previous_channels(self):
        """
        doc
        """
        if self.wi and self.wi.previous and self.wi.previous.channels:
            return self.wi.previous.channels
        else 
            return []
        
#     and self.wi.previous.metadata:
#             return [x for x in experiment.metadata 
#                     if 'type' in experiment.metadata[x] 
#                     and experiment.metadata[x]['type'] == "channel"]
#         else:
#             return []
         
    # MAGIC: provides dynamically updated values for the "conditions" trait
    def _get_previous_conditions(self):
        """
        doc
        """
        if self.wi and self.wi.previous and self.wi.previous.conditions:
            return self.wi.previous.conditions.keys()
        else:
            return []
    
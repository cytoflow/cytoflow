"""
Created on Mar 15, 2015

@author: brian
"""
from traits.api import Interface, Str, HasTraits, Instance, Property, \
                       cached_property
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

    def get_operation(self, wi):
        """
        Return an instance of the IOperation that this plugin wraps
        """
        
#     def get_ui(self, wi):
#         """
#         Return a traitsui View for the IOperation this plugin wraps
#         
#         There's a lot of logic you can stuff into a view (enums, visible_when,
#         etc.)  If you need more logic, though, feel free to define a Controller
#         and use that to handle, eg, button presses or derived traits (eg,
#         with a Property trait)
#         
#         Parameters
#         ----------
#         wi : WorkflowItem
#             the WorkflowItem that wraps this Operation; lets us access the 
#             previous and current operation results.
#         """

    def get_icon(self):
        """
        doc
        """
        
class OpWrapperMixin(HasTraits):
    wi = Instance(WorkflowItem)
    
    # a Property wrapper around the wi.previous.result.channels
    # used to constrain the operation view (with an EnumEditor)
    previous_channels = Property(depends_on = 'wi.previous.result.channels')
    
    @cached_property
    def _get_previous_channels(self):
        if (not self.wi.previous) or (not self.wi.previous.result):
            return []
              
        return self.wi.previous.result.channels
    
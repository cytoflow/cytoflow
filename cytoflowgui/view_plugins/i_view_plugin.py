"""
Created on Mar 15, 2015

@author: brian
"""

from traits.api import Interface, Str, HasTraits, Property, Instance, List
from cytoflowgui.workflow_item import WorkflowItem

VIEW_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.view_plugins'

class IViewPlugin(Interface):
    """
    
    Attributes
    ----------
    
    id : Str
        The envisage ID used to refer to this plugin
        
    view_id : Str
        Same as the "id" attribute of the IView this plugin wraps
        Prefix: edu.mit.synbio.cytoflowgui.view
        
    short_name : Str
        The view's "short" name - for menus, toolbar tips, etc.
    """
    
    view_id = Str
    short_name = Str

    def get_view(self):
        """Return an IView instance that this plugin wraps"""


class ViewHandlerMixin(HasTraits):
    """
    Common bits useful for View wrappers.
    """
     
    channels = Property(List, depends_on = 'wi.channels')
    conditions = Property(List, depends_on = 'wi.conditions')
    
    wi = Instance(WorkflowItem)

    # MAGIC: provides dynamically updated values for the "channels" trait
    def _get_channels(self):
        """
        doc
        """
        return self.wi.channels
         
    # MAGIC: provides dynamically updated values for the "conditions" trait
    def _get_conditions(self):
        """
        doc
        """
        ret = [""]
        ret.extend(self.wi.conditions)
        return ret

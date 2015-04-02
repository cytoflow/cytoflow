"""
Created on Mar 15, 2015

@author: brian
"""

from traits.api import Interface, Str, HasTraits, Property, Instance, \
                       DelegatesTo
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
        pass
    
    def get_ui(self, wi):
        """
        Return an instance of a traitsui View for the view we wrap.
        
        There's a lot of logic you can stuff into a view (enums, visible_when,
        etc.)  If you need more logic, though, feel free to define a Controller
        and use that to handle, eg, button presses or derived traits (eg,
        with a Property trait)
        
        Parameters
        ----------
        wi : WorkflowItem
            The WorkflowItem whose result this view is viewing; to set 
            EnumEditors, etc.
        """

class ViewHandlerMixin(HasTraits):
    """
    Common bits useful for View handlers.
    """
    
    channels = Property
    conditions = Property
    
    wi = Instance(WorkflowItem)

    # MAGIC: provides dynamically updated values for the "channels" trait
    def _get_channels(self):
        """
        doc
        """
        return self.wi.result.channels
        
    # MAGIC: provides dynamically updated values for the "conditions" trait
    def _get_conditions(self):
        """
        doc
        """
        ret = [""]
        ret.extend(self.wi.result.conditions.keys())
        return ret
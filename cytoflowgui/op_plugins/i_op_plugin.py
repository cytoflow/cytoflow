"""
Created on Mar 15, 2015

@author: brian
"""
from traits.api import Interface, Str

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
        Return an instance of the IOperation that this plugin wraps
        """
        
    def get_ui(self, model):
        """
        Return a traitsui View for the IOperation this plugin wraps
        
        There's a lot of logic you can stuff into a view (enums, visible_when,
        etc.)  If you need more logic, though, feel free to define a Controller
        and use that to handle, eg, button presses or derived traits (eg,
        with a Property trait)
        """

    def get_icon(self):
        """
        doc
        """
        
    
class MOperationPlugin(object):
    """ 
    A mixin class containing common code for implementations of IOperationPlugin
    """
    
    pass
    
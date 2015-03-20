"""
Created on Mar 15, 2015

@author: brian
"""
from traits.api import Interface, Str

OP_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.op_plugins'

class IOperationPlugin(Interface):
    """
    classdocs
    """
    
    short_name = Str
    menu_group = Str

    def get_operation(self):
        """
        doc
        """
        
    def get_view(self):
        """
        Return an instance of a traitsui View for the operation we wrap.
        
        There's a lot of logic you can stuff into a view (enums, visible_when,
        etc.)  If you need more logic, though, feel free to define a Handler
        (especially a ModelView) and use that to handle, eg, button presses.
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
    
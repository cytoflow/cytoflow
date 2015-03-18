"""
Created on Mar 15, 2015

@author: brian
"""
from traits.api import Interface, Str

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
            
    def get_handler(self):
        """
        doc
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
    
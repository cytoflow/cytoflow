"""
Created on Mar 15, 2015

@author: brian
"""
from traits.api import Interface

class IOperationPlugin(Interface):
    """
    classdocs
    """

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
        

"""
Created on Mar 15, 2015

@author: brian
"""

from traits.api import Interface

class IViewPlugin(Interface):
    """
    classdocs
    """

    def get_view(self):
        pass
    
    def get_handler(self):
        pass
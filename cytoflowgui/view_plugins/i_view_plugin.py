"""
Created on Mar 15, 2015

@author: brian
"""

from traits.api import Interface, Str

VIEW_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.view_plugins'

class IViewPlugin(Interface):
    """
    classdocs
    """
    
    short_name = Str

    def get_view(self):
        pass
    
    def get_traitsui_view(self, model):
        """
        Return an instance of a traitsui View for the view we wrap.
        
        There's a lot of logic you can stuff into a view (enums, visible_when,
        etc.)  If you need more logic, though, feel free to define a Controller
        and use that to handle, eg, button presses or derived traits (eg,
        with a Property trait)
        """
    
class MViewPlugin(object):
    """
    A mixin class containing common code for implementations of IViewPlugin
    """
    pass
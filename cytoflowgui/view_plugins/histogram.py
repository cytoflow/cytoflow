"""
Created on Feb 24, 2015

@author: brian
"""

from traitsui.api import View, Item
from envisage.api import Plugin, contributes_to
from traits.api import provides

from cytoflow import HistogramView
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, MViewPlugin, VIEW_PLUGIN_EXT

@provides(IViewPlugin)
class HistogramPlugin(Plugin, MViewPlugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.histogram'
    name = "Histogram"
    
    def get_view(self):
        return HistogramView()
    
    def get_traitsui_view(self, model):
        return View(Item('object.name'),
                    Item('object.channel'),
                    Item('object.xfacet'),
                    Item('object.yfacet'),
                    Item('object.huefacet'),
                    Item('object.subset'))

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
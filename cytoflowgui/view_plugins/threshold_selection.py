'''
Created on Mar 21, 2015

@author: brian
'''

from traitsui.api import View, Item
from envisage.api import Plugin, contributes_to
from traits.api import provides

from cytoflow import ThresholdSelection
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, MViewPlugin, VIEW_PLUGIN_EXT

@provides(IViewPlugin)
class ThresholdSelectionPlugin(Plugin, MViewPlugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.threshold_selection'
    name = "Threshold"
    
    def get_view(self):
        return ThresholdSelection()
    
    def get_traitsui_view(self, model):
        return View(Item('object.view.name'),
                    Item('object.view.channel'),
                    Item('object.view.xfacet'),
                    Item('object.view.yfacet'),
                    Item('object.view.huefacet'),
                    Item('object.view.subset'))

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
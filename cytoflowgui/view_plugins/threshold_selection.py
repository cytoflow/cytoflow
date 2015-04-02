'''
Created on Mar 21, 2015

@author: brian
'''

from traitsui.api import View, Item
from envisage.api import Plugin, contributes_to
from traits.api import provides

from cytoflow import ThresholdSelection
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT

@provides(IViewPlugin)
class ThresholdSelectionPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.threshold'
    view_id = 'edu.mit.synbio.cytoflow.view.threshold'
    short_name = "Threshold"
    
    def get_view(self):
        return ThresholdSelection()
    
    def get_ui(self, wi):
        return View(Item('object.view.name'),
                    Item('object.view.channel'),
                    Item('object.view.xfacet'),
                    Item('object.view.yfacet'),
                    Item('object.view.huefacet'),
                    Item('object.view.subset'))

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
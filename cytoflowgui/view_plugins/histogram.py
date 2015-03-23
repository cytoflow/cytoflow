"""
Created on Feb 24, 2015

@author: brian
"""

from traitsui.api import View, Item, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Property, Instance

from cytoflow import HistogramView
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, MViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin
    
class HistogramHandler(Controller, ViewHandlerMixin):
    """
    docs
    """
    pass
    

@provides(IViewPlugin)
class HistogramPlugin(Plugin, MViewPlugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.histogram'
    view_id = 'edu.mit.synbio.cytoflow.view.histogram'
    short_name = "Histogram"
    
    def get_view(self):
        return HistogramView()
    
    def get_ui(self, wi):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor=EnumEditor(name='handler.channels'),
                         label = "Channel"),
                    Item('object.xfacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label = "Horizontal\nFacet"),
                    Item('object.yfacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label = "Vertical\nFacet"),
                    Item('object.huefacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label="Color\nFacet"),
                    handler = HistogramHandler(wi = wi))

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
"""
Created on Feb 24, 2015

@author: brian
"""

from traitsui.api import View, Item, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable
from pyface.api import ImageResource

from cytoflow import HistogramView
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin
    
class HistogramHandler(Controller, ViewHandlerMixin):
    """
    docs
    """
    
    def default_traits_view(self):
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
                    Item('_'),
                    Item('object.subset',
                         label="Subset",
                         editor = SubsetEditor(experiment = "handler.wi.result")))
    
class HistogramPluginView(HistogramView, PluginViewMixin):
    handler_factory = Callable(HistogramHandler)

@provides(IViewPlugin)
class HistogramPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.histogram'
    view_id = 'edu.mit.synbio.cytoflow.view.histogram'
    short_name = "Histogram"
    
    def get_view(self):
        return HistogramPluginView()
    
    def get_icon(self):
        return ImageResource('histogram')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
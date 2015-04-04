"""
Created on Feb 24, 2015

@author: brian
"""

from traitsui.api import View, Item, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Property, Instance, DelegatesTo

from cytoflow import HistogramView
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.subset_model import SubsetModel
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewWrapperMixin
    
class HistogramViewWrapper(HistogramView, ViewWrapperMixin):
    """
    docs
    """
    
    def default_traits_view(self):
        return View(Item('name'),
            Item('channel',
                 editor=EnumEditor(name='channels'),
                 label = "Channel"),
            Item('xfacet',
                 editor=EnumEditor(name='conditions'),
                 label = "Horizontal\nFacet"),
            Item('yfacet',
                 editor=EnumEditor(name='conditions'),
                 label = "Vertical\nFacet"),
            Item('huefacet',
                 editor=EnumEditor(name='conditions'),
                 label="Color\nFacet"),
            Item('_'),
            Item('subset',
                 label="Subset",
                 editor = SubsetEditor(experiment = "object.wi.result")))

@provides(IViewPlugin)
class HistogramPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.histogram'
    view_id = 'edu.mit.synbio.cytoflow.view.histogram'
    short_name = "Histogram"
    
    def get_view(self, wi):
        return HistogramViewWrapper(wi = wi)

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
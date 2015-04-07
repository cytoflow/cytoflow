'''
Created on Mar 21, 2015

@author: brian
'''

from traitsui.api import View, Item, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, DelegatesTo

from cytoflow import ThresholdSelection, HistogramView
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin
from cytoflowgui.subset_editor import SubsetEditor
    
class ThresholdHandler(Controller, ViewHandlerMixin):
    """
    docs
    """
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channel',
                         editor = EnumEditor(name = 'handler.channels'),
                         label = "Channel"),
                    Item('object.xfacet',
                         editor = EnumEditor(name = 'handler.conditions'),
                         label = "Horizontal\nFacet"),
                    Item('object.yfacet',
                         editor = EnumEditor(name = 'handler.conditions'),
                         label = "Vertical\nFacet"),
                    Item('object.huefacet',
                         editor = EnumEditor(name = 'handler.conditions'),
                         label = "Color\nFacet"),
                    Item('_'),
                    Item('object.subset',
                         label = "Subset",
                         editor = SubsetEditor(experiment = 'handler.wi.result')))
    

@provides(IViewPlugin)
class ThresholdSelectionPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.threshold'
    view_id = 'edu.mit.synbio.cytoflow.view.threshold'
    short_name = "Threshold"
    
    def get_view(self):
        view = ThresholdSelection(view = HistogramView())
        view.add_trait('name', DelegatesTo('view'))
        view.add_trait('channel', DelegatesTo('view'))
        view.add_trait('xfacet', DelegatesTo('view'))
        view.add_trait('yfacet', DelegatesTo('view'))
        view.add_trait('huefacet', DelegatesTo('view'))
        view.add_trait('subset', DelegatesTo('view'))
        view.handler_factory = ThresholdHandler
        return view

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
'''
Created on Mar 21, 2015

@author: brian
'''

from traitsui.api import View, Item, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, DelegatesTo, Callable

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
    
class ThresholdSelectionView(ThresholdSelection):

    handler_factory = Callable(ThresholdHandler)
    
    def __init__(self, **kwargs):
        super(ThresholdSelectionView, self).__init__(**kwargs)
        
        self.view = HistogramView()
        self.add_trait('name', DelegatesTo('view'))
        self.add_trait('channel', DelegatesTo('view'))
        self.add_trait('xfacet', DelegatesTo('view'))
        self.add_trait('yfacet', DelegatesTo('view'))
        self.add_trait('huefacet', DelegatesTo('view'))
        self.add_trait('subset', DelegatesTo('view'))
        
    def is_wi_valid(self, wi):
        return (wi.previous 
                and wi.previous.result 
                and self.is_valid(wi.previous.result))
    
    def plot_wi(self, wi, pane):
        pane.plot(wi.previous.result, self)        
    

@provides(IViewPlugin)
class ThresholdSelectionPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.threshold'
    view_id = 'edu.mit.synbio.cytoflow.view.threshold'
    short_name = "Threshold"
    
    def get_view(self):
        return ThresholdSelectionView()

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
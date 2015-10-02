"""
Created on Feb 24, 2015

@author: brian
"""

from traitsui.api import View, Item, Controller, EnumEditor, Handler
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Instance, Dict
from pyface.api import ImageResource

from cytoflow import Stats1DView, geom_mean
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin
    
import numpy as np
import scipy.stats
    
class Stats1DHandler(Controller, ViewHandlerMixin):
    """
    docs
    """
    
    summary_functions = Dict({np.mean : "Mean",
                             # TODO - add count and proportion
                             geom_mean : "Geom.Mean",
                             len : "Count"})
    
    spread_functions = Dict({np.std : "Std.Dev.",
                             scipy.stats.sem : "S.E.M"
                       # TODO - add 95% CI
                       })
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.xvariable',
                         editor=EnumEditor(name='handler.conditions'),
                         # TODO - restrict this to NUMERIC values?
                         label = "X Variable"),
                    Item('object.ychannel',
                         editor=EnumEditor(name='handler.channels'),
                         label = "Y Channel"),
                    Item('object.yfunction',
                         editor = EnumEditor(name='handler.summary_functions'),
                         label = "Y Summary\nFunction"),
                    Item('object.xfacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label = "Horizontal\nFacet"),
                    Item('object.yfacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label = "Vertical\nFacet"),
                    Item('object.huefacet',
                         editor=EnumEditor(name='handler.conditions'),
                         label="Color\nFacet"),
#                     Item('object.error_bars',
#                          editor = EnumEditor(values = {None : "",
#                                                        "data" : "Data",
#                                                        "summary" : "Summary"}),
#                          label = "Error bars?"),
#                     Item('object.error_function',
#                          editor = EnumEditor(name='handler.spread_functions'),
#                          label = "Error bar\nfunction",
#                          visible_when = 'object.error_bars is not None'),
#                     Item('object.error_var',
#                          editor = EnumEditor(name = 'handler.conditions'),
#                          label = "Error bar\nVariable",
#                          visible_when = 'object.error_bars == "summary"'),
                    Item('_'),
                    Item('object.subset',
                         label="Subset",
                         editor = SubsetEditor(experiment = "handler.wi.result")))
    
class Stats1DPluginView(Stats1DView):
    handler = Instance(Handler, transient = True)
    handler_factory = Callable(Stats1DHandler)
    
    def plot_wi(self, wi, pane):
        pane.plot(wi.result, self)

@provides(IViewPlugin)
class Stats1DPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.stats1d'
    view_id = 'edu.mit.synbio.cytoflow.view.stats1d'
    short_name = "1D Statistics View"
    
    def get_view(self):
        return Stats1DPluginView()

    def get_icon(self):
        return ImageResource('stats_1d')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
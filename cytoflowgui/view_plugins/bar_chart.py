"""
Created on Feb 24, 2015

@author: brian
"""

from traitsui.api import View, Item, Controller, EnumEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Dict
from pyface.api import ImageResource

from cytoflow import BarChartView, geom_mean
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin
    
import numpy as np
import scipy.stats
    
class BarChartHandler(Controller, ViewHandlerMixin):
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
                    Item('object.channel',
                         editor=EnumEditor(name='handler.channels'),
                         label = "Channel"),
                    Item('object.variable',
                         editor=EnumEditor(name='handler.conditions'),
                         label = "Variable"),
                    Item('object.function',
                         editor = EnumEditor(name='handler.summary_functions'),
                         label = "Summary\nFunction"),
                    # TODO - waiting on seaborn v0.6
#                    Item('object.orientation')
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
    
class BarChartPluginView(BarChartView, PluginViewMixin):
    handler_factory = Callable(BarChartHandler)

@provides(IViewPlugin)
class BarChartPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.barchart'
    view_id = 'edu.mit.synbio.cytoflow.view.barchart'
    short_name = "Bar Chart"
    
    def get_view(self):
        return BarChartPluginView()

    def get_icon(self):
        return ImageResource('bar_chart')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
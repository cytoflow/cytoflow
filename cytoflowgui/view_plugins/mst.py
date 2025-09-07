#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Minimum spanning tree plot
--------------------------

Plots a minimum spanning tree of a statistic. 

    * The default behavior will produce a tree where each vertex is a circle 
      and the color of the circle is related to the intensity of the 
      value of ``Feature``. (In this scenario, ``Variable`` must be left empty.)
      
    * Setting ``Style`` to ``Pie plot`` will draw a pie plot at each vertex. The values 
      of `Variable` are used as the categories of the pie, and the arc length 
      of each slice of pie is related to the intensity of the value of ``Feature``.
      
    * Setting ``Style`` to ``Petal plot`` will draw a "petal plot" at each vertex. The 
      values of `Variable` are used as the categories, but unlike a pie plot, the 
      arc width of each slice is equal. Instead, the radius of the pie slice scales 
      with the square root of the intensity, so that the relationship between area and
      intensity remains the same.
      
      
    Optionally, you can set ``Scale by events`` to scale the total size of each
    circle, pie or petal plot by the number of events that match the category.

.. object:: Statistic

    Which statistic to plot. This is usually the name of the operation that 
    added the statistic. 
    
.. object:: Style

    Which style view to plot?
    
.. object:: Feature

    Which column in the statistic should be plotted?
    
.. object:: Variable

    The statistic variable to classify segments in ``pie`` or ``petal`` plots.
    
.. object:: Locations

    A second statistic whose features (columns) are the locations of the 
    vertices. Usually produced by a clustering module such as as ``KMeans`` 
    or ``SOM``.
    
.. object:: Locations Level

    If there are multiple index levels in the ``Locations`` statistic, which one
    is different at each location? Optional if there is only one level in 
    ``Locations``.
        
.. object:: Locations Features

    Which features in ``Locations`` should be used as vertex positions? (By
    default, use all of them.)
    
.. object:: Scale

    How to scale the color, arc length or radii of the plots.
    
.. object:: Subset

    Plot only a subset of the statistic.
    
.. object:: Scale by Events

    If set, scale each circle/pie/petal by the number of matching events.
    
.. plot::
   :include-source: False
   
    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()
        
    km = flow.KMeansOp(name = "KMeans",
                       channels = ["V2-A", "Y2-A", "B1-A"],
                       scale = {"V2-A" : "logicle",
                               "Y2-A" : "logicle",
                               "B1-A" : "logicle"},
                       num_clusters = 20)       
    km.estimate(ex)
    ex2 = km.apply(ex)

    ex3 = flow.ChannelStatisticOp(name = "ByDox",
                                  channel = "Y2-A",
                                  by = ["KMeans_Cluster", "Dox"],
                                  function = len).apply(ex2) 
                                  
    flow.MSTView(statistic = "ByDox", 
        locations = "KMeans", 
        locations_features = ["V2-A", "Y2-A", "B1-A"],
        feature = "Y2-A",
        variable = "Dox",
        style = "pie").plot(ex3)
        
"""

import pandas as pd

from traits.api import provides, Property, List
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller, CheckListEditor
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..workflow.views import MSTWorkflowView, MSTPlotParams
from ..workflow.views.view_base import COLORMAPS
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin, BasePlotParamsView

METRICS = ['euclidean', 'cosine', 'braycurtis', 'canberra', 'chebyshev', 'cityblock', 'correlation', 
           'dice', 'hamming', 'jaccard', 'jensenshannon', 'kulczynski1', 'mahalanobis', 
           'matching', 'minkowski', 'rogerstanimoto', 'russellrao', 'seuclidean', 
           'sokalmichener', 'sokalsneath', 'sqeuclidean', 'yule']

class MSTParamsHandler(Controller):
    view_params_view = BasePlotParamsView
    view_params_view = \
        View(Item('title',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('legendlabel',
                  label = "Hue label",
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('sns_style',
                  label = "Style"),
             Item('sns_context',
                  label = "Context"),
             Item('legend',
                  label = "Show legend?"),
             Item('palette',
                  label = "Color palette",
                  editor = EnumEditor(values = {'' : '0:(Default)'} | COLORMAPS)))
        
class MSTHandler(ViewHandler):
  
    features = Property(depends_on = "context.statistics, model.statistic")
    locations_features = Property(depends_on = "context.statistics, model.locations")
    locations_levels = Property(depends_on = "context.statistics, model.locations")
    indices = Property(depends_on = "context.statistics, model.statistic, model.subset")
    levels = Property(depends_on = "context.statistics, model.statistic")

    view_traits_view = \
        View(VGroup(
             VGroup(Item('statistic',
                         editor=EnumEditor(name='context_handler.statistics_names'),
                         label = "Statistic"),
                    Item('style',
                         editor = EnumEditor(values = {'heat' : "Heat Map",
                                                       'pie' : "Pie Plot",
                                                       'petal' : "Petal Plot"}),
                         label = "Style"),
                    Item('feature',
                         editor = EnumEditor(name = 'handler.features'),
                         label = "Feature"),
                    Item('variable',
                         editor=ExtendableEnumEditor(name='handler.indices',
                                                     extra_items = {"None" : ""}),
                         label = "Variable"),
                    Item('locations',
                         editor = EnumEditor(name = 'context_handler.statistics_names'),
                         label = "Locations"),
                    Item('locations_level',
                         editor = EnumEditor(name = 'handler.locations_levels'),
                         label = "Locations\nLevel",
                         visible_when = "len(handler.locations_levels) > 1"),
                    Item('locations_features',
                         editor = CheckListEditor(name = 'handler.locations_features'),
                         label = "Locations\nFeatures",
                         style = 'custom'),
                    Item('scale', label = "Scale"),
                    Item('scale_by_events', label = "Scale by events"),
                    Item('metric',
                         editor = EnumEditor(values = METRICS)),
                    label = "Min Spanning Tree",
                    show_border = False),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "handler.levels",
                                                   editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                  handler_factory = subset_handler_factory),
                                                   mutable = False)),
                    label = "Subset",
                    show_border = False,
                    show_labels = False),
             Item('context.view_warning',
                  resizable = True,
                  visible_when = 'context.view_warning',
                  editor = ColorTextEditor(foreground_color = "#000000",
                                          background_color = "#ffff99")),
             Item('context.view_error',
                  resizable = True,
                  visible_when = 'context.view_error',
                  editor = ColorTextEditor(foreground_color = "#000000",
                                           background_color = "#ff9191"))))
        
    view_params_view = \
        View(Item('plot_params',
                  editor = InstanceHandlerEditor(view = 'view_params_view',
                                                 handler_factory = MSTParamsHandler),
                  style = 'custom',
                  show_label = False))
        
    # MAGIC: gets the value for the property "features"
    def _get_features(self):
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return []
         
        stat = self.context.statistics[self.model.statistic]
        return stat.columns.to_list()
    
    # MAGIC: gets the value for the property 'location_features'
    def _get_locations_features(self):
        if not (self.context and self.context.statistics 
                and self.model.locations in self.context.statistics):
            return []
         
        locs = self.context.statistics[self.model.locations]
        return locs.columns.to_list()

    # MAGIC: gets the value for the property 'location_levels'
    def _get_locations_levels(self):
        if not (self.context and self.context.statistics 
                and self.model.locations in self.context.statistics):
            return []
         
        locs = self.context.statistics[self.model.locations]
        return locs.index.names
    
        
    # MAGIC: gets the value for the property indices
    def _get_indices(self):
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return []
         
        stat = self.context.statistics[self.model.statistic]
         
        if self.model.subset:
            stat = stat.query(self.model.subset)
             
        if len(stat) == 0:
            return []       
         
        names = list(stat.index.names)
        for name in names:
            unique_values = stat.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                stat.index = stat.index.droplevel(name)
         
        return list(stat.index.names)
     
    # MAGIC: gets the value for the property 'levels'
    # returns a Dict(Str, pd.Series)
     
    def _get_levels(self):        
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return {}
         
        stat = self.context.statistics[self.model.statistic]
        index = stat.index
         
        names = list(index.names)
        for name in names:
            unique_values = index.get_level_values(name).unique()
            if len(unique_values) == 1:
                index = index.droplevel(name)
 
        names = list(index.names)
        ret = {}
        for name in names:
            ret[name] = pd.Series(index.get_level_values(name)).sort_values()
            ret[name] = pd.Series(ret[name].unique())
             
        return ret
    
     


@provides(IViewPlugin)
class MSTPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.view.mst'
    view_id = 'cytoflow.view.mst'
    name = "Minimum Spanning Tree"
    short_name = "MST"
    
    def get_view(self):
        return MSTWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, MSTWorkflowView):
            return MSTHandler(model = model, context = context)
        elif isinstance(model, MSTPlotParams):
            return MSTParamsHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('mst')

    plugin = List(contributes_to = VIEW_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
    




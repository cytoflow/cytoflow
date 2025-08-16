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
Matrix Chart
------------

Plots a "matrix" chart. This can be a heat map, or a matrix of pie or petal plots:

    * The default behavior will produce a "traditional" heat map, where each "cell" 
      is a circle and the color of the circle is related to the intensity of the 
      value of ``Feature``. (In this scenario, ``Variable`` must be left empty.)
      
    * Setting ``Style`` to ``Pie plot`` will draw a pie plot in each cell. The values 
      of `Variable` are used as the categories of the pie, and the arc length 
      of each slice of pie is related to the intensity of the value of ``Feature``.
      
    * Setting ``Style`` to ``Petal plot`` will draw a "petal plot" in each cell. The 
      values of `Variable` are used as the categories, but unlike a pie plot, the 
      arc width of each slice is equal. Instead, the radius of the pie slice scales 
      with the square root of the intensity, so that the relationship between area and
      intensity remains the same.
      
    Optionally, you can set ``Scale by events`` to scale the total size of each
    circle, pie or petal plot by the number of events that match the category.

.. object:: Statistic

    Which statistic to plot. This is usually the name of the operation that 
    added the statistic. 
    
.. object:: Horizontal Facet

    What statistic variable should be plotted in the columns of the matrix plot?
    If left unset, there will only be one column.
        
.. object:: Vertical Facet

    What statistic variable should be plotted in the rows of the matrix plot?
    If left unset, there will only be one row.
    
.. object:: Feature

    Which column in the statistic should be plotted?
    
.. object:: Variable

    The statistic variable to classify segments in ``pie`` or ``petal`` plots.
    
.. object:: Style

    Which style matrix view to plot?
    
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
    
    ex2 = flow.ThresholdOp(name = 'Threshold',
                           channel = 'Y2-A',
                           threshold = 2000).apply(ex)
        

    ex3 = flow.ChannelStatisticOp(name = "ByDox",
                                  channel = "Y2-A",
                                  by = ['Dox', 'Threshold'],
                                  function = len).apply(ex2) 

    flow.MatrixView(statistic = "ByDox",
                    xfacet = 'Dox',
                    variable = 'Threshold',
                    feature = 'Y2-A',
                    style = 'pie').plot(ex3)
        
"""

import pandas as pd

from traits.api import provides, Property, List
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..workflow.views import MatrixWorkflowView, MatrixPlotParams
from ..workflow.views.view_base import COLORMAPS
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin, BasePlotParamsView


class MatrixParamsHandler(Controller):
    view_params_view = \
        View(Item('title',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('xlabel',
                  label = "X label",
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('ylabel',
                  label = "Y label",
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

        
class MatrixHandler(ViewHandler):
  
    features = Property(depends_on = "context.statistics, model.statistic")
    indices = Property(depends_on = "context.statistics, model.statistic, model.subset")
    levels = Property(depends_on = "context.statistics, model.statistic")

    view_traits_view = \
        View(VGroup(
             VGroup(Item('statistic',
                         editor=EnumEditor(name='context_handler.statistics_names'),
                         label = "Statistic"),
                    Item('feature',
                         editor = EnumEditor(name = 'handler.features'),
                         label = "Feature"),
                    Item('xfacet',
                         editor=ExtendableEnumEditor(name='handler.indices',
                                                     extra_items = {"None" : ""}),
                         label = "Horizontal\nFacet"),
                    Item('yfacet',
                         editor=ExtendableEnumEditor(name='handler.indices',
                                                     extra_items = {"None" : ""}),
                         label = "Vertical\nFacet"),
                    Item('variable',
                         editor=ExtendableEnumEditor(name='handler.indices',
                                                     extra_items = {"None" : ""}),
                         label = "Variable"),
                    Item('style',
                         editor = EnumEditor(values = {'heat' : "Heat Map",
                                                       'pie' : "Pie Plot",
                                                       'petal' : "Petal Plot"}),
                         label = "Style"),
                    Item('scale', label = "Scale"),
                    Item('scale_by_events', label = "Scale by events"),
                    label = "Matrix",
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
                                                 handler_factory = MatrixParamsHandler),
                  style = 'custom',
                  show_label = False))
        
    # MAGIC: gets the value for the property "features"
    def _get_features(self):
        if not (self.context and self.context.statistics 
                and self.model.statistic in self.context.statistics):
            return []
         
        stat = self.context.statistics[self.model.statistic]
        return stat.columns.to_list()
        
        
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
class MatrixPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.view.matrix'
    view_id = 'cytoflow.view.matrix'
    name = "Matrix View"
    short_name = "Matrix"
    
    def get_view(self):
        return MatrixWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, MatrixWorkflowView):
            return MatrixHandler(model = model, context = context)
        elif isinstance(model, MatrixPlotParams):
            return MatrixParamsHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('matrix')

    plugin = List(contributes_to = VIEW_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
    


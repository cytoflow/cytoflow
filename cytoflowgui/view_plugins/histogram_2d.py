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
2D Histogram
------------

Plots a 2-dimensional histogram.  Similar to a density plot, but the number of
events in a bin change the bin's opacity, so you can use different colors.

.. object:: X Channel, Y Channel

    The channels to plot on the X and Y axes.
    
.. object:: X Scale, Y Scale

    How to scale the X and Y axes of the plot.
    
.. object:: Horizonal Facet

    Make multiple plots.  Each column has a unique value of this variable.
    
.. object:: Vertical Facet

    Make multiple plots.  Each row has a unique value of this variable.
    
.. object:: Color Facet

    Plot with multiple colors.  Each color has a unique value of this variable.
    
.. object:: Color Scale

    If **Color Facet** is a numeric variable, use this scale for the color
    bar.
    
.. object:: Tab Facet

    Make multiple plots in differen tabs; each tab's plot has a unique value
    of this variable.
    
.. object:: Subset

    Plot only a subset of the data in the experiment.
    
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

    flow.Histogram2DView(xchannel = 'V2-A',
                         xscale = 'log',
                         ychannel = 'Y2-A',
                         yscale = 'log',
                         huefacet = 'Dox').plot(ex)

"""

from traits.api import provides, List
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..workflow.views import Histogram2DWorkflowView, Histogram2DPlotParams
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin, Data2DPlotParamsView


class Histogram2DParamsHandler(Controller):
    view_params_view = \
        View(Item('gridsize',
                  editor = TextEditor(auto_set = False),
                  label = "Grid size"),
             Item('smoothed',
                  label = "Smooth"),
             Item('smoothed_sigma',
                  editor = TextEditor(auto_set = False),
                  label = "Smooth\nsigma",
                  visible_when = "smoothed == True"),
             Data2DPlotParamsView.content)


class Histogram2DHandler(ViewHandler):

    view_traits_view = \
        View(VGroup(
             VGroup(Item('xchannel',
                         editor=EnumEditor(name='context_handler.channels'),
                         label = "X Channel"),
                    Item('xscale',
                         label = "X Scale"),
                    Item('ychannel',
                         editor=EnumEditor(name='context_handler.channels'),
                         label = "Y Channel"),
                    Item('yscale',
                         label = "Y Scale"),
                    Item('xfacet',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names',
                                                     extra_items = {"None" : ""}),
                         label = "Horizontal\nFacet"),
                    Item('yfacet',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names',
                                                     extra_items = {"None" : ""}),
                         label = "Vertical\nFacet"),
                    Item('huefacet',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names',
                                                     extra_items = {"None" : ""}),
                         label="Color\nFacet"),
                    Item('huescale',
                         label = "Color\nScale"),
                    Item('plotfacet',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names',
                                                     extra_items = {"None" : ""}),
                         label = "Tab\nFacet"),
                    label = "2D Histogram",
                    show_border = False),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.conditions",
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
                                                 handler_factory = Histogram2DParamsHandler),
                  style = 'custom',
                  show_label = False))



@provides(IViewPlugin)
class Histogram2DPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.view.histogram2d'
    view_id = 'cytoflow.view.histogram2d'
    name = "2D Histogram"

    def get_view(self):
        return Histogram2DWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, Histogram2DWorkflowView):
            return Histogram2DHandler(model = model, context = context)
        elif isinstance(model, Histogram2DPlotParams):
            return Histogram2DParamsHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('histogram_2d')

    plugin = List(contributes_to = VIEW_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]
        


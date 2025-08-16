#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022 2015-2017
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
Violin Plot
-----------

Plots a violin plot, which is a nice way to compare several distributions.

.. object:: X Variable

    The variable to compare on the X axis.

.. object:: Y Channel

    The channel to plot on the Y axis.
    
.. object:: Y Channel Scale

    How to scale the Y axis of the plot.
    
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

    flow.ViolinPlotView(channel = 'Y2-A',
                        scale = 'log',
                        variable = 'Dox').plot(ex)
"""

from traits.api import provides, List
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..workflow.views import ViolinPlotWorkflowView, ViolinPlotParams
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin, Data1DPlotParamsView


class ViolinParamsHandler(Controller):        
    view_params_view = \
        View(Item('bw',
                  label = 'Bandwidth'),
             Item('scale_plot',
                  label = "Plot scale"),
             Item('scale_hue'),
             Item('gridsize',
                  editor = TextEditor(auto_set = False)),
             Item('inner'),
             Item('split'),
             Data1DPlotParamsView.content)
        
    
class ViolinHandler(ViewHandler):

    view_traits_view = \
        View(VGroup(
             VGroup(Item('variable',
                         editor=ExtendableEnumEditor(name='context_handler.conditions_names'),
                         label = "X Variable"),
                    Item('channel',
                         editor=EnumEditor(name='context_handler.channels'),
                         label = "Y Channel"),
                    Item('scale',
                         label = "Y Channel\nScale"),
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
                      label = "Violin Plot",
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
                                                 handler_factory = ViolinParamsHandler),
                  style = 'custom',
                  show_label = False))

    
@provides(IViewPlugin)
class ViolinPlotPlugin(Plugin, PluginHelpMixin):

    id = 'cytoflowgui.view_plugins.violin'
    view_id = 'cytoflow.view.violin'
    name = "Violin Plot"
    short_name = "Violin"

    def get_view(self):
        return ViolinPlotWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, ViolinPlotWorkflowView):
            return ViolinHandler(model = model, context = context)
        elif isinstance(model, ViolinPlotParams):
            return ViolinParamsHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('violin')

    plugin = List(contributes_to = VIEW_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]

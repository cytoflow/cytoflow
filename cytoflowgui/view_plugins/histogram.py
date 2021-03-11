#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
Histogram
------------

Plots a histogram.

.. object:: Channel

    The channel for the plot.
    
.. object:: Scale

    How to scale the X axis of the plot.
    
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
        
    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()

    flow.HistogramView(channel = 'Y2-A',
                       scale = 'log',
                       huefacet = 'Dox').plot(ex)
"""

from traits.api import provides
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller, HGroup
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflowgui.workflow.views.histogram import HistogramWorkflowView, HistogramPlotParams

from cytoflowgui.editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .subset_controllers import subset_handler_factory
from ..editors import TabListEditor
from .view_plugin_base import ViewHandler, PluginHelpMixin, Data1DPlotParamsView


class HistogramParamsHandler(Controller):
    view_params_view = \
        View(Item('num_bins',
                  editor = TextEditor(auto_set = False,
                                      format_func = lambda x: "" if x == None else str(x))),
             Item('histtype'),
             Item('linestyle'),
             Item('linewidth',
                  editor = TextEditor(auto_set = False,
                                      format_func = lambda x: "" if x == None else str(x))),
             Item('density'),
             Item('alpha',
                  editor = TextEditor(auto_set = False)),
             Data1DPlotParamsView.content)
        

class HistogramHandler(ViewHandler):

    view_traits_view = \
        View(VGroup(VGroup(Item('channel',
                                editor=EnumEditor(name='context.channels'),
                                label = "Channel"),
                           Item('scale'),
                           Item('xfacet',
                                editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                            extra_items = {"None" : ""}),
                                label = "Horizontal\nFacet"),
                            Item('yfacet',
                                editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                            extra_items = {"None" : ""}),
                                label = "Vertical\nFacet"),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                           Item('huescale',
                                label = "Color\nScale"),
                           Item('plotfacet',
                                editor=ExtendableEnumEditor(name='handler.conditions_names',
                                                            extra_items = {"None" : ""}),
                                label = "Tab\nFacet"),
                            label = "Histogram Plot",
                            show_border = False),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.conditions",
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
                                                 handler_factory = HistogramParamsHandler),
                  style = 'custom',
                  show_label = False))

    

@provides(IViewPlugin)
class HistogramPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.view.histogram'
    view_id = 'edu.mit.synbio.cytoflow.view.histogram'
    short_name = "Histogram"
    
    def get_view(self):
        return HistogramWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, HistogramWorkflowView):
            return HistogramHandler(model = model, context = context)
        elif isinstance(model, HistogramPlotParams):
            return HistogramParamsHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('histogram')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self


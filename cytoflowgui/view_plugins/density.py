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

from traits.api import provides
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from ..workflow.views import DensityWorkflowView, DensityPlotParams
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..subset_controllers import subset_handler_factory

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler, PluginHelpMixin, Data2DPlotParamsView


class DensityParamsHandler(Controller):
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
        

class DensityHandler(ViewHandler):
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
                                                 handler_factory = DensityParamsHandler),
                  style = 'custom',
                  show_label = False))
        

@provides(IViewPlugin)
class DensityPlugin(Plugin, PluginHelpMixin):
    id = 'edu.mit.synbio.cytoflowgui.view.density'
    view_id = 'edu.mit.synbio.cytoflow.view.density'
    short_name = "Density Plot"

    def get_view(self):
        return DensityWorkflowView()
    
    def get_handler(self, model, context):
        if isinstance(model, DensityWorkflowView):
            return DensityHandler(model = model, context = context)
        elif isinstance(model, DensityPlotParams):
            return DensityParamsHandler(model = model, context = context)
    
    def get_icon(self):
        return ImageResource('density')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
        


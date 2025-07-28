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

'''
Polygon Gate
------------

Draw a polygon gate.  To add vertices, use a single-click; to close the
polygon, click the first vertex a second time.

.. object:: Name

    The operation name.  Used to name the new metadata field that's created by 
    this module.
    
.. object:: X Channel

    The name of the channel on the gate's X axis.

.. object:: Y Channel

    The name of the channel on the gate's Y axis.
    
.. object:: X Scale

    The scale of the X axis for the interactive plot.
    
.. object:: Y Scale

    The scale of the Y axis for the interactive plot
    
.. object:: Hue facet

    Show different experimental conditions in different colors.
    
.. object:: Subset

    Show only a subset of the data.
   
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

    p = flow.PolygonOp(name = "Polygon",
                       xchannel = "V2-A",
                       ychannel = "Y2-A")
    p.vertices = [(23.411982294776319, 5158.7027015021222), 
                  (102.22182270573683, 23124.058843387455), 
                  (510.94519955277201, 23124.058843387455), 
                  (1089.5215641232173, 3800.3424832180476), 
                  (340.56382570202402, 801.98947404942271), 
                  (65.42597937575897, 1119.3133482602157)]

    p.default_view(huefacet = "Dox",
                   xscale = 'log',
                   yscale = 'log').plot(ex)

'''

from traits.api import provides, List
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..view_plugins import ViewHandler
from ..view_plugins.view_plugin_base import Data2DPlotParamsView
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..workflow.operations import PolygonWorkflowOp, PolygonSelectionView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin

class PolygonViewParamsHandler(Controller):
    view_params_view = \
        View(Item('density'),
             # density-specific
             Item('gridsize',
                  editor = TextEditor(auto_set = False),
                  visible_when = 'density',
                  label = "Grid size"),
             Item('smoothed',
                  visible_when = 'density',
                  label = "Smooth"),
             Item('smoothed_sigma',
                  editor = TextEditor(auto_set = False),
                  label = "Smooth\nsigma",
                  visible_when = "density and smoothed"),
             
             # scatterplot-specific
             Item('alpha',
                  editor = TextEditor(auto_set = False),
                  visible_when = 'not density'),
             Item('s',
                  editor = TextEditor(auto_set = False),
                  visible_when = 'not density',
                  label = "Size"),
             Item('marker',
                  visible_when = 'not density'),
             Data2DPlotParamsView.content)

class PolygonHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False)),
             Item('xchannel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "X Channel"),
             Item('ychannel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "Y Channel"),
             shared_op_traits_view) 
        
        
class PolygonViewHandler(ViewHandler):
    view_traits_view = \
        View(VGroup(
             VGroup(Item('xchannel', 
                         label = "X Channel", 
                         style = 'readonly'),
                    Item('xscale',
                         label = "X Scale"),
                    Item('ychannel',
                         label = "Y Channel",
                         style = 'readonly'),
                    Item('yscale',
                         label = "Y Scale"),
                    Item('huefacet',
                         editor=ExtendableEnumEditor(name='context_handler.previous_conditions_names',
                                                     extra_items = {"None" : ""}),
                         visible_when = 'not plot_params.density',
                         label="Color\nFacet"),
                    Item('huescale',
                         visible_when = 'plot_params.density',
                         label = "Color\nScale"),
                    label = "Polygon Setup View",
                    show_border = False),
             VGroup(Item('subset_list',
                         show_label = False,
                         editor = SubsetListEditor(conditions = "context_handler.previous_conditions",
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
                                                 handler_factory = PolygonViewParamsHandler),
                  style = 'custom',
                  show_label = False))
        



@provides(IOperationPlugin)
class PolygonPlugin(Plugin, PluginHelpMixin):
    
    id = 'cytoflowgui.op_plugins.polygon'
    operation_id = 'cytoflow.operations.polygon'
    view_id = 'cytoflowgui.workflow.operations.polygonview'

    name = "Polygon Gate"
    menu_group = "Gates"
    
    def get_operation(self):
        return PolygonWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, PolygonWorkflowOp):
            return PolygonHandler(model = model, context = context)
        elif isinstance(model, PolygonSelectionView):
            return PolygonViewHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('polygon')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]

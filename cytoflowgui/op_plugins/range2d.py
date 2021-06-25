#!/usr/bin/env python3.8
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


'''
2D Range Gate
-------------

Draw a 2-dimensional range gate (eg, a rectangle).  To set the gate, 
click-and-drag on the plot.

.. object:: Name

    The operation name.  Used to name the new metadata field that's created by 
    this operation.
        
.. object:: X channel

    The name of the channel on the X axis.
        
.. object:: X Low

    The low threshold in the X channel.

.. object:: X High

    The high threshold in the X channel.

.. object:: Y channel

    The name of the channel on the Y axis.
        
.. object:: Y Low

    The low threshold in the Y channel.

.. object:: Y High

    The high threshold in the Y channel.

.. object:: X Scale

    The scale of the X axis for the interactive plot.
    
.. object:: Y Scale

    The scale of the Y axis for the interactive plot
    
.. object:: Hue facet

    Show different experimental conditions in different colors.
    
.. object:: Subset

    Show only a subset of the data.
        
.. plot::
    
    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()

    r = flow.Range2DOp(name = "Range2D",
                       xchannel = "V2-A",
                       xlow = 10,
                       xhigh = 1000,
                       ychannel = "Y2-A",
                       ylow = 1000,
                       yhigh = 20000)

    r.default_view(huefacet = "Dox",
                   xscale = 'log',
                   yscale = 'log').plot(ex)
'''

from traits.api import provides
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from ..view_plugins import ViewHandler
from ..view_plugins.scatterplot import ScatterplotParamsHandler
from ..editors import SubsetListEditor, ColorTextEditor, ExtendableEnumEditor, InstanceHandlerEditor
from ..workflow.operations import Range2DWorkflowOp, Range2DSelectionView
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin


class Range2DHandler(OpHandler):
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False)),
             Item('xchannel',
                  editor=EnumEditor(name='context_handler.previous_channels'),
                  label = "X Channel"),
             Item('xlow', 
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),                  
                  label = "X Low"),
             Item('xhigh', 
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),                  
                  label = "X High"),
             Item('ychannel',
                  editor=EnumEditor(name='context_handler.previous_channels'),               
                  label = "Y Channel"),
             Item('ylow', 
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "Y Low"),
             Item('yhigh', 
                  editor = TextEditor(auto_set = False,
                                      evaluate = float,
                                      format_func = lambda x: "" if x is None else str(x),
                                      placeholder = "None"),
                  label = "Y High"),
             shared_op_traits_view) 
        
        
class Range2DViewHandler(ViewHandler):
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
                         label="Color\nFacet"),
                    label = "2D Range Setup View",
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
                                                 handler_factory = ScatterplotParamsHandler),
                  style = 'custom',
                  show_label = False))


@provides(IOperationPlugin)
class Range2DPlugin(Plugin, PluginHelpMixin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.range2d'
    operation_id = 'edu.mit.synbio.cytoflow.operations.range2d'
    view_id = 'edu.mit.synbio.cytoflow.views.range2d'

    short_name = "Range 2D"
    menu_group = "Gates"
    
    def get_operation(self):
        return Range2DWorkflowOp()
    
    def get_handler(self, model, context):
        if isinstance(model, Range2DWorkflowOp):
            return Range2DHandler(model = model, context = context)
        elif isinstance(model, Range2DSelectionView):
            return Range2DViewHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('range2d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    


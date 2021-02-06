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

'''
Quadrant Gate
-------------

Draw a "quadrant" gate.  To create a new gate, just click where you'd like the
intersection to be.  Creates a new metadata **Name**, with values ``name_1``,
``name_2``, ``name_3``, ``name_4`` ordered **clockwise from upper-left.**

.. note::

    This matches the order of FACSDiva quad gates.
    

.. object:: Name

    The operation name.  Used to name the new metadata field that's created by 
    this operation.
        
.. object:: X channel

    The name of the channel on the X axis.
        
.. object:: X threshold

    The threshold in the X channel.

.. object:: Y channel

    The name of the channel on the Y axis.
        
.. object:: Y threshold

    The threshold in the Y channel.

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

    quad = flow.QuadOp(name = "Quad",
                       xchannel = "V2-A",
                       xthreshold = 100,
                       ychannel = "Y2-A",
                       ythreshold = 1000)

    qv = quad.default_view(xscale = 'log', yscale = 'log')
    qv.plot(ex)
'''

from traits.api import provides, Callable, Instance, Str, DelegatesTo, CFloat
from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.quad import QuadOp, QuadSelection

from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, PluginOpMixin, OP_PLUGIN_EXT, shared_op_traits, PluginHelpMixin
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.view_plugins.scatterplot import ScatterplotPlotParams
from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

QuadOp.__repr__ = traits_repr

class QuadHandler(OpHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('xchannel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "X Channel"),
                    Item('xthreshold',
                         editor = TextEditor(auto_set = False),
                         label = "X Threshold"),
                    Item('ychannel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Y Channel"),
                    Item('ythreshold',
                         editor = TextEditor(auto_set = False),
                         label = "Y Threshold"),
                    shared_op_traits) 
        
class ThresholdViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('xchannel', 
                                label = "X Channel",
                                style = "readonly"),
                           Item('xthreshold', 
                                label = "X Threshold",
                                style = "readonly"),
                           Item('xscale'),
                           Item('ychannel', 
                                label = "Y Channel",
                                style = "readonly"),
                           Item('ythreshold', 
                                label = "Y Threshold",
                                style = "readonly"),
                           Item('yscale'),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='handler.previous_conditions_names',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                           label = "Quad Setup View",
                           show_border = False),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "handler.previous_conditions")),
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

class QuadSelectionView(PluginViewMixin, QuadSelection):
    handler_factory = Callable(ThresholdViewHandler, transient = True)    
    op = Instance(IOperation, fixed = True)
    xthreshold = DelegatesTo('op', status = True)
    ythreshold = DelegatesTo('op', status = True)
    plot_params = Instance(ScatterplotPlotParams, ()) 

    name = Str
    
    def should_plot(self, changed, payload):
        if changed == Changed.PREV_RESULT or changed == Changed.VIEW:
            return True
        else:
            return False
        
    def plot_wi(self, wi):        
        self.plot(wi.previous_wi.result, **self.plot_params.trait_get())
        
    def get_notebook_code(self, idx):
        view = QuadSelection()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx}{plot_params})
        """
        .format(idx = idx, 
                traits = traits_str(view),
                prev_idx = idx - 1,
                plot_params = ", " + plot_params_str if plot_params_str else ""))
    
class QuadPluginOp(QuadOp, PluginOpMixin):
    handler_factory = Callable(QuadHandler, transient = True)
    xthreshold = CFloat
    ythreshold = CFloat

    def default_view(self, **kwargs):
        return QuadSelectionView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        op = QuadOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))

@provides(IOperationPlugin)
class QuadPlugin(Plugin, PluginHelpMixin): 
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.quad'
    operation_id = 'edu.mit.synbio.cytoflow.operations.quad'

    short_name = "Quad"
    menu_group = "Gates"
    
    def get_operation(self):
        return QuadPluginOp()

    def get_icon(self):
        return ImageResource(u'quad')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
@camel_registry.dumper(QuadPluginOp, 'quad', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                xthreshold = op.xthreshold,
                ychannel = op.ychannel,
                ythreshold = op.ythreshold)
    
@camel_registry.loader('quad', version = 1)
def _load(data, version):
    return QuadPluginOp(**data)

@camel_registry.dumper(QuadSelectionView, 'quad-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                xscale = view.xscale,
                yscale = view.yscale,
                huefacet = view.huefacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(QuadSelectionView, 'quad-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op,
                xscale = view.xscale,
                yscale = view.yscale,
                huefacet = view.huefacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('quad-view', version = any)
def _load_view(data, version):
    return QuadSelectionView(**data)
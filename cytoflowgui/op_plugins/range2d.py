#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
Created on Apr 25, 2015

@author: brian
'''

from traits.api import provides, Callable, Str, Instance, DelegatesTo
from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.range2d import Range2DOp, RangeSelection2D
from cytoflow.views.i_selectionview import ISelectionView

from cytoflowgui.op_plugins.i_op_plugin \
    import IOperationPlugin, OpHandlerMixin, PluginOpMixin, OP_PLUGIN_EXT, shared_op_traits, PluginHelpMixin
from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

Range2DOp.__repr__ = traits_repr

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

class Range2DHandler(OpHandlerMixin, Controller):
    
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('xchannel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "X Channel"),
                    Item('xlow', 
                         editor = TextEditor(auto_set = False),
                         label = "X Low"),
                    Item('xhigh', 
                         editor = TextEditor(auto_set = False),
                         label = "X High"),
                    Item('ychannel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Y Channel"),
                    Item('ylow', 
                         editor = TextEditor(auto_set = False),
                         label = "Y Low"),
                    Item('yhigh', 
                         editor = TextEditor(auto_set = False),
                         label = "Y High"),
                    shared_op_traits) 
        
class RangeView2DHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
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
                                editor=ExtendableEnumEditor(name='handler.previous_conditions_names',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                           label = "2D Range Setup View",
                           show_border = False),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous_conditions")),
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

@provides(ISelectionView)
class Range2DSelectionView(PluginViewMixin, RangeSelection2D):
    handler_factory = Callable(RangeView2DHandler, transient = True)
    op = Instance(IOperation, fixed = True)
    xlow = DelegatesTo('op', status = True)
    xhigh = DelegatesTo('op', status = True)
    ylow = DelegatesTo('op', status = True)
    yhigh = DelegatesTo('op', status = True)
    name = Str
    
    def should_plot(self, changed, payload):
        if changed == Changed.PREV_RESULT or changed == Changed.VIEW:
            return True
        else:
            return False
    
    def plot_wi(self, wi):
        self.plot(wi.previous_wi.result)
        
    def get_notebook_code(self, idx):
        view = RangeSelection2D()
        view.copy_traits(self, view.copyable_trait_names())
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx})
        """
        .format(idx = idx, 
                traits = traits_str(view),
                prev_idx = idx - 1))
    
    
class Range2DPluginOp(Range2DOp, PluginOpMixin):
    handler_factory = Callable(Range2DHandler, transient = True)
    
    def default_view(self, **kwargs):
        return Range2DSelectionView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        op = Range2DOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))

@provides(IOperationPlugin)
class Range2DPlugin(Plugin, PluginHelpMixin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.range2d'
    operation_id = 'edu.mit.synbio.cytoflow.operations.range2d'

    short_name = "Range 2D"
    menu_group = "Gates"
    
    def get_operation(self):
        return Range2DPluginOp()

    def get_icon(self):
        return ImageResource('range2d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
@camel_registry.dumper(Range2DPluginOp, 'range2d', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                xlow = op.xlow,
                xhigh = op.xhigh,
                ychannel = op.ychannel,
                ylow = op.ylow,
                yhigh = op.yhigh)
    
@camel_registry.loader('range2d', version = 1)
def _load(data, version):
    return Range2DPluginOp(**data)

@camel_registry.dumper(Range2DSelectionView, 'range2d-view', version = 1)
def _dump_view(view):
    return dict(op = view.op,
                xscale = view.xscale,
                yscale = view.yscale,
                huefacet = view.huefacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('range2d-view', version = 1)
def _load_view(data, version):
    return Range2DSelectionView(**data)
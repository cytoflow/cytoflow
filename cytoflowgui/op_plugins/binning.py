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
Binning
-------

Bin data along an axis.

This operation creates equally spaced bins (in linear or log space)
along an axis and adds a condition assigning each event to a bin.  The
value of the event's condition is the left end of the bin's interval in
which the event is located.

.. object:: Name

    The name of the new condition created by this operation.
    
.. object:: Channel

    The channel to apply the binning to.
    
.. object:: Scale

    The scale to apply to the channel before binning.
    
.. object:: Num Bins

    How many (equi-spaced) bins to create?  Must set either **Num Bins** or
    **Bin Width**.  If both are set, **Num Bins** takes precedence.
    
.. object:: Bin Width

    How wide should each bin be?  Can only set if **Scale** is *linear* or
    *log* (in which case, **Bin Width** is in log10-units.)

.. plot::

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
    ex = import_op.apply()

    bin_op = flow.BinningOp()
    bin_op.name = "Bin"
    bin_op.channel = "FITC-A"
    bin_op.scale = "log"
    bin_op.bin_width = 0.2

    ex2 = bin_op.apply(ex)

    bin_op.default_view().plot(ex2) 
'''

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Str, Instance, DelegatesTo
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.binning import BinningOp, BinningView
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

BinningOp.__repr__ = traits_repr

class BinningHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Channel"),
                    Item('scale'),
                    Item('bin_width',
                         editor = TextEditor(auto_set = False),
                         label = "Bin Width"),
                    shared_op_traits)

class BinningPluginOp(PluginOpMixin, BinningOp):
    handler_factory = Callable(BinningHandler)
    
    def default_view(self, **kwargs):
        return BinningPluginView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        op = BinningOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))

class BinningViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('channel',
                                style = 'readonly'),
                           Item('huefacet',
                                style = 'readonly'),
                           label = "Binning Default Plot",
                           show_border = False)),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "handler.context.previous_wi.conditions")),
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
                                                  background_color = "#ff9191")))

@provides(IView)
class BinningPluginView(PluginViewMixin, BinningView):
    handler_factory = Callable(BinningViewHandler)
    op = Instance(IOperation, fixed = True)
    huefacet = Str(status = True)
    huescale = DelegatesTo('op', 'scale', status = True)
    
    def plot_wi(self, wi):
        if wi.result is not None:
            self.plot(wi.result)
        else:
            self.plot(wi.previous_wi.result)
            
    def get_notebook_code(self, idx):
        view = BinningView()
        view.copy_traits(self, view.copyable_trait_names())
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{idx})
        """
        .format(idx = idx,
                traits = traits_str(view)))


@provides(IOperationPlugin)
class BinningPlugin(Plugin, PluginHelpMixin):
 
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.binning'
    operation_id = 'edu.mit.synbio.cytoflow.operations.binning'

    short_name = "Binning"
    menu_group = "Gates"
    
    def get_operation(self):
        return BinningPluginOp()
    
    def get_icon(self):
        return ImageResource('binning')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
### Serialization
@camel_registry.dumper(BinningPluginOp, 'binning', version = 1)
def _dump(op):
    return dict(name = op.name,
                channel = op.channel,
                scale = op.scale,
                num_bins = op.num_bins,
                bin_width = op.bin_width)
    
@camel_registry.loader('binning', version = 1)
def _load(data, version):
    return BinningPluginOp(**data)

@camel_registry.dumper(BinningPluginView, 'binning-view', version = 1)
def _dump_view(view):
    return dict(op = view.op,
                subset_list = view.subset_list)

@camel_registry.loader('binning-view', version = 1)
def _load_view(data, version):
    return BinningPluginView(**data)


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
Density 
-------

Computes a gate based on a 2D density plot.  The user chooses what proportion
of events to keep, and the module creates a gate that selects those events in
the highest-density bins of a 2D density histogram.
    
A single gate may not be appropriate for an entire experiment.  If this is the 
case, you can use **By** to specify metadata by which to aggregate the data 
before computing and applying the gate.  
    
.. object:: Name
        
    The operation name; determines the name of the new metadata
        
.. object:: X Channel, Y Channel
    
    The channels to apply the mixture model to.

.. object:: X Scale, Y Scale 

    Re-scale the data in **Channel** before fitting. 

.. object:: Keep

    The proportion of events to keep in the gate.  Defaults to 0.9.
    
.. object:: By 

    A list of metadata attributes to aggregate the data before estimating
    the model.  For example, if the experiment has two pieces of metadata,
    ``Time`` and ``Dox``, setting :attr:`by` to ``["Time", "Dox"]`` will fit 
    the model separately to each subset of the data with a unique combination of
    ``Time`` and ``Dox``.

.. plot::

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()
    

    density_op = flow.DensityGateOp(name = 'Density',
                                    xchannel = 'FSC-A',
                                    xscale = 'log',
                                    ychannel = 'SSC-A',
                                    yscale = 'log',
                                    keep = 0.5)
    density_op.estimate(ex)   
    density_op.default_view().plot(ex)
    ex2 = density_op.apply(ex)
'''

import numpy as np

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, List, Str, Instance, Property, 
                        on_trait_change)
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations import IOperation
from cytoflow.operations.density import DensityGateOp, DensityGateView
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.view_plugins.density import DensityPlotParams
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

DensityGateOp.__repr__ = traits_repr

class DensityGateHandler(OpHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('xchannel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "X Channel"),
                    Item('ychannel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Y Channel"),
                    Item('xscale',
                         label = "X Scale"),
                    Item('yscale',
                         label = "Y Scale"),
                    VGroup(
                    Item('keep', 
                         editor = TextEditor(auto_set = False),
                         label = "Proportion\nto keep"),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'handler.previous_conditions_names'),
                         label = 'Group\nEstimates\nBy',
                         style = 'custom'),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous_wi.conditions")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    label = "Estimation parameters",
                    show_border = False),
                    shared_op_traits)

class DensityGatePluginOp(PluginOpMixin, DensityGateOp):
    handler_factory = Callable(DensityGateHandler)
    
    # add "estimate" metadata
    xchannel = Str(estimate = True)
    ychannel = Str(estimate = True)
    keep = util.PositiveCFloat(0.9, allow_zero = False, estimate = True)
    by = List(Str, estimate = True)
    xscale = util.ScaleEnum(estimate = True)
    yscale = util.ScaleEnum(estimate = True)
        
    # bits to support the subset editor
    
    subset_list = List(ISubset, estimate = True)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change('subset_list.str')
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))

    def default_view(self, **kwargs):
        return DensityGatePluginView(op = self, **kwargs)
    
    def estimate(self, experiment):
        try:
            super().estimate(experiment, subset = self.subset)
        except:
            raise
        finally:
            self.changed = (Changed.ESTIMATE_RESULT, self)
    
    def clear_estimate(self):
        self._xscale = self._yscale = None
        self._xbins = np.empty(1)
        self._ybins = np.empty(1)
        self._keep_xbins = dict()
        self._keep_ybins = dict()
        self._histogram = {}

        self.changed = (Changed.ESTIMATE_RESULT, self)
        
    def should_clear_estimate(self, changed, payload):
        return True
            
    def get_notebook_code(self, idx):
        op = DensityGateOp()
        op.copy_traits(self, op.copyable_trait_names())      

        return dedent("""
        op_{idx} = {repr}
        
        op_{idx}.estimate(ex_{prev_idx}{subset})
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1,
                subset = ", subset = " + repr(self.subset) if self.subset else ""))

class DensityGateViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('xchannel',
                                style = 'readonly'),
                           Item('ychannel',
                                style = 'readonly'),
                           Item('xscale',
                                style = 'readonly'),
                           Item('yscale',
                                style = 'readonly'),
                           Item('huescale'),
                           label = "Density Gate Default Plot",
                           show_border = False)),
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
class DensityGatePluginView(PluginViewMixin, DensityGateView):
    handler_factory = Callable(DensityGateViewHandler)
    op = Instance(IOperation, fixed = True)
    plot_params = Instance(DensityPlotParams, ())
#     subset = DelegatesTo('op', transient = True)
#     by = DelegatesTo('op', status = True)
#     xchannel = DelegatesTo('op', 'xchannel', transient = True)
#     xscale = DelegatesTo('op', 'xscale', transient = True)
#     ychannel = DelegatesTo('op', 'ychannel', transient = True)
#     yscale = DelegatesTo('op', 'yscale', transient = True)
    
    
    def should_plot(self, changed, payload):
        """
        Should the owning WorkflowItem refresh the plot when certain things
        change?  `changed` can be:
        - Changed.VIEW -- the view's parameters changed
        - Changed.RESULT -- this WorkflowItem's result changed
        - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
        - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed

        """
        if changed == Changed.RESULT:
            return False
        
        return True
    
    def plot_wi(self, wi):
        if self.plot_names:
            self.plot(wi.previous_wi.result, 
                      plot_name = self.current_plot,
                      **self.plot_params.trait_get())
        else:
            self.plot(wi.previous_wi.result,
                      **self.plot_params.trait_get())
        
    def enum_plots_wi(self, wi):
        try:
            return self.enum_plots(wi.previous_wi.result)
        except:
            return []
            
    def get_notebook_code(self, idx):
        view = DensityGateView()
        view.copy_traits(self, view.copyable_trait_names())
        view.subset = self.subset
        plot_params_str = traits_str(self.plot_params)
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{idx}{plot_params})
        """
        .format(traits = traits_str(view),
                idx = idx,
                plot_params = ", " + plot_params_str if plot_params_str else ""))
    

@provides(IOperationPlugin)
class DensityGatePlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.density'
    operation_id = 'edu.mit.synbio.cytoflow.operations.density'

    short_name = "2D Mixture Model"
    menu_group = "Gates"
    
    def get_operation(self):
        return DensityGatePluginOp()
    
    def get_icon(self):
        return ImageResource('density')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
@camel_registry.dumper(DensityGatePluginOp, 'density-gate', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                ychannel = op.ychannel,
                xscale = op.xscale,
                yscale = op.yscale,
                keep = op.keep,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('density-gate', version = 1)
def _load(data, version):
    return DensityGatePluginOp(**data)

@camel_registry.dumper(DensityGatePluginView, 'density-gate-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(DensityGatePluginView, 'density-gate-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op)

@camel_registry.loader('density-gate-view', version = any)
def _load_view(data, ver):
    return DensityGatePluginView(**data)

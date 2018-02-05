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
FlowPeaks
---------

This module uses the **flowPeaks** algorithm to assign events to clusters in
an unsupervized manner.
    
.. object:: Name
        
    The operation name; determines the name of the new metadata
        
.. object:: X Channel, Y Channel
    
    The channels to apply the mixture model to.

.. object:: X Scale, Y Scale 

    Re-scale the data in **Channel** before fitting. 

.. object:: h, h0

    Scalar values that control the smoothness of the estimated distribution.
    Increasing **h** makes it "rougher," while increasing **h0** makes it
    smoother.
    
.. object:: tol

    How readily should clusters be merged?  Must be between 0 and 1.
    
.. object:: Merge Distance

    How far apart can clusters be before they are merged?
    
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
    

    fp_op = flow.FlowPeaksOp(name = 'Flow',
                             channels = ['V2-A', 'Y2-A'],
                             scale = {'V2-A' : 'log',
                                      'Y2-A' : 'log'})
    fp_op.estimate(ex)   
    ex2 = fp_op.apply(ex)
    fp_op.default_view(density = True).plot(ex2)
    fp_op.default_view().plot(ex2)

'''

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, List, Str, Bool, Instance, Constant,
                        DelegatesTo, Property, on_trait_change)
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations import IOperation
from cytoflow.operations.flowpeaks import FlowPeaksOp, FlowPeaks2DView, FlowPeaks2DDensityView
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

FlowPeaksOp.__repr__ = traits_repr

class FlowPeaksHandler(OpHandlerMixin, Controller):
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
                    Item('h', 
                         editor = TextEditor(auto_set = False)),
                    Item('h0',
                         editor = TextEditor(auto_set = False)),
                    Item('tol',
                         editor = TextEditor(auto_set = False)),
                    Item('merge_dist',
                         editor = TextEditor(auto_set = False),
                         label = "Merge\nDistance"),
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

class FlowPeaksPluginOp(PluginOpMixin, FlowPeaksOp):
    handler_factory = Callable(FlowPeaksHandler)

    # add "estimate" metadata
    xchannel = Str(estimate = True)
    ychannel = Str(estimate = True)
    xscale = util.ScaleEnum(estimate = True)
    yscale = util.ScaleEnum(estimate = True)
    h = util.PositiveFloat(1.5, allow_zero = False, estimate = True)
    h0 = util.PositiveFloat(1, allow_zero = False, estimate = True)
    tol = util.PositiveFloat(0.5, allow_zero = False, estimate = True)
    merge_dist = util.PositiveFloat(5, allow_zero = False, estimate = True)
    
    by = List(Str, estimate = True)
        
    # bits to support the subset editor
    
    subset_list = List(ISubset, estimate = True)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change('subset_list.str')
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))
        

    @on_trait_change('xchannel, ychannel')
    def _channel_changed(self):
        self.channels = []
        self.scale = {}
        if self.xchannel:
            self.channels.append(self.xchannel)
            
            if self.xchannel in self.scale:
                del self.scale[self.xchannel]
                
            self.scale[self.xchannel] = self.xscale
            
        if self.ychannel:
            self.channels.append(self.ychannel)
            
            if self.ychannel in self.scale:
                del self.scale[self.ychannel]
            
            self.scale[self.ychannel] = self.yscale

        
    @on_trait_change('xscale, yscale')
    def _scale_changed(self):
        self.scale = {}

        if self.xchannel:
            self.scale[self.xchannel] = self.xscale
            
        if self.ychannel:
            self.scale[self.ychannel] = self.yscale
            

    def default_view(self, **kwargs):
        return FlowPeaksPluginView(op = self, **kwargs)
    
    def estimate(self, experiment):
        if not self.xchannel:
            raise util.CytoflowOpError('xchannel',
                                       "Must set X channel")
            
        if not self.ychannel:
            raise util.CytoflowOpError('ychannel',
                                       "Must set Y channel")
            
        super().estimate(experiment, subset = self.subset)
        self.changed = (Changed.ESTIMATE_RESULT, self)
    
    def clear_estimate(self):
        self._kmeans.clear()
        self._normals.clear()
        self._density.clear()
        self._peaks.clear()
        self._cluster_peak.clear()
        self._cluster_group.clear()
        self._scale.clear()
        
        self.changed = (Changed.ESTIMATE_RESULT, self)
    
    def get_notebook_code(self, idx):
        op = FlowPeaksOp()
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

class FlowPeaksViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('xchannel',
                                style = 'readonly'),
                           Item('ychannel',
                                style = 'readonly'),
                           Item('show_density',
                                label = "Show density plot?"),
                           label = "Flow Peaks Default Plot",
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
class FlowPeaksPluginView(PluginViewMixin):
    handler_factory = Callable(FlowPeaksViewHandler)
    op = Instance(IOperation, fixed = True)
    subset = DelegatesTo('op', transient = True)
    by = DelegatesTo('op', status = True)
    xchannel = DelegatesTo('op', 'xchannel', transient = True)
    xscale = DelegatesTo('op', 'xscale', transient = True)
    ychannel = DelegatesTo('op', 'ychannel', transient = True)
    yscale = DelegatesTo('op', 'yscale', transient = True)
    
    show_density = Bool(False)

    
    id = "edu.mit.synbio.cytoflowgui.op_plugins.flowpeaks"
    friendly_id = "FlowPeaks" 
    
    name = Constant("FlowPeaks")
    
    def plot(self, experiment, **kwargs):
        if self.show_density:
            FlowPeaks2DDensityView(op = self.op,
                                   xchannel = self.xchannel,
                                   ychannel = self.ychannel,
                                   xscale = self.xscale,
                                   yscale = self.yscale).plot(experiment, 
                                                              **kwargs)
        else:
            FlowPeaks2DView(op = self.op,
                            xchannel = self.xchannel,
                            ychannel = self.ychannel,
                            xscale = self.xscale,
                            yscale = self.yscale).plot(experiment, 
                                                       **kwargs)
            
        
    def plot_wi(self, wi):
        if wi.result:
            if self.plot_names:
                self.plot(wi.result, plot_name = self.current_plot)
            else:
                self.plot(wi.result)
        else:
            if self.plot_names:
                self.plot(wi.previous_wi.result, plot_name = self.current_plot)
            else:
                self.plot(wi.previous_wi.result)
        
    def enum_plots_wi(self, wi):
        if wi.result:
            try:
                return self.enum_plots(wi.result)
            except:
                return []
        else:
            try:
                return self.enum_plots(wi.previous_wi.result)
            except:
                return []
            
    def get_notebook_code(self, idx):
        view = FlowPeaks2DView()
        view.copy_traits(self, view.copyable_trait_names())
        view.subset = self.subset
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{idx})
        """
        .format(traits = traits_str(view),
                idx = idx))
    

@provides(IOperationPlugin)
class FlowPeaksPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.flowpeaks'
    operation_id = 'edu.mit.synbio.cytoflow.operations.flowpeaks'

    short_name = "Flow Peaks"
    menu_group = "Gates"
    
    def get_operation(self):
        return FlowPeaksPluginOp()
    
    def get_icon(self):
        return ImageResource('flowpeaks')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
@camel_registry.dumper(FlowPeaksPluginOp, 'flowpeaks', version = 1)
def _dump(op):
    return dict(name = op.name,
                xchannel = op.xchannel,
                ychannel = op.ychannel,
                xscale = op.xscale,
                yscale = op.yscale,
                h = op.h,
                h0 = op.h0,
                tol = op.tol,
                merge_dist = op.merge_dist,
                subset_list = op.subset_list)
    
@camel_registry.loader('flowpeaks', version = 1)
def _load(data, version):
    return FlowPeaksPluginOp(**data)

@camel_registry.dumper(FlowPeaksPluginView, 'flowpeaks-view', version = 1)
def _dump_view(view):
    return dict(op = view.op,
                show_density = view.show_density)

@camel_registry.loader('flowpeaks-view', version = 1)
def _load_view(data, ver):
    return FlowPeaksPluginView(**data)
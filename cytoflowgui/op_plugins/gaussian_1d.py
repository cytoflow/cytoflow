#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
Gaussian Mixture Model (1D)
---------------------------

Fit a Gaussian mixture model with a specified number of components to one 
channel.

If **Num Components** is greater than 1, then this module creates a new 
categorical metadata variable named **Name**, with possible values 
``{name}_1`` .... ``name_n`` where ``n`` is the number of components.  
An event is assigned to  ``name_i`` category if it has the highest posterior 
probability of having been produced by component ``i``.  If an event has a 
value that is outside the range of one of the channels' scales, then it is 
assigned to ``{name}_None``.
    
Additionally, if **Sigma** is greater than 0, this module creates new  boolean
metadata variables named ``{name}_1`` ... ``{name}_n`` where ``n`` is the 
number of components.  The column ``{name}_i`` is ``True`` if the event is less 
than **Sigma** standard deviations from the mean of component ``i``.  If 
**Num Components** is ``1``, **Sigma** must be greater than 0.
    
Finally, the same mixture model (mean and standard deviation) may not
be appropriate for every subset of the data.  If this is the case, you
can use **By** to specify metadata by which to aggregate the data before 
estimating and applying a mixture model.  

.. note:: 

    **Num Components** and **Sigma** withh be the same for each subset. 
    
.. object:: Name
        
    The operation name; determines the name of the new metadata
        
.. object:: Channel
    
    The channels to apply the mixture model to.

.. object:: Scale 

    Re-scale the data in **Channel** before fitting. 

.. object:: Num Components

    How many components to fit to the data?  Must be a positive integer.

.. object:: Sigma 
    
    How many standard deviations on either side of the mean to include
    in the boolean variable ``{name}_i``?  Must be ``>= 0.0``.  If 
    **Num Components** is ``1``, must be ``> 0``.
    
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
    

    gm_op = flow.GaussianMixtureOp(name = 'Gauss',
                                   channels = ['Y2-A'],
                                   scale = {'Y2-A' : 'log'},
                                   num_components = 2)

    gm_op.estimate(ex) 
    ex2 = gm_op.apply(ex)

    gm_op.default_view().plot(ex2)
'''

from sklearn import mixture

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, \
                         CheckListEditor, ButtonEditor, TextEditor
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, Instance, Str, List, Dict, Any, 
                        DelegatesTo, Property, on_trait_change, Constant)
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.gaussian import GaussianMixtureOp, GaussianMixture1DView
from cytoflow.views.i_selectionview import IView
import cytoflow.utility as util

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.view_plugins.histogram import HistogramPlotParams
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.ext_enum_editor import ExtendableEnumEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.workflow import Changed
from cytoflowgui.serialization import camel_registry, traits_repr, traits_str, dedent

GaussianMixtureOp.__repr__ = traits_repr

class GaussianMixture1DHandler(OpHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Channel"),
                    Item('channel_scale',
                         label = "Scale"),
                    VGroup(
                    Item('num_components', 
                         editor = TextEditor(auto_set = False),
                         label = "Num\nComponents"),
                    Item('sigma',
                         editor = TextEditor(auto_set = False)),
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

class GaussianMixture1DPluginOp(PluginOpMixin, GaussianMixtureOp):
    id = Constant('edu.mit.synbio.cytoflowgui.operations.gaussian_1d')

    handler_factory = Callable(GaussianMixture1DHandler)
    
    channel = Str
    channel_scale = util.ScaleEnum(estimate = True)
    
    # add "estimate" metadata
    num_components = util.PositiveCInt(1, estimate = True)
    sigma = util.PositiveCFloat(0.0, allow_zero = True, estimate = True)
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
    
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True)

    @on_trait_change('channel')
    def _channel_changed(self):
        self.channels = [self.channel]
        self.changed = (Changed.ESTIMATE, ('channels', self.channels))

        if self.channel_scale:
            self.scale = {self.channel : self.channel_scale}
            self.changed = (Changed.ESTIMATE, ('scale', self.scale))
        
    @on_trait_change('channel_scale')
    def _scale_changed(self):
        if self.channel:
            self.scale = {self.channel : self.channel_scale}
        self.changed = (Changed.ESTIMATE, ('scale', self.scale))
    
    def estimate(self, experiment):
        try:
            super().estimate(experiment, subset = self.subset)
        except:
            raise
        finally:
            self.changed = (Changed.ESTIMATE_RESULT, self)
    
    def default_view(self, **kwargs):
        return GaussianMixture1DPluginView(op = self, 
                                           **kwargs)
    
    
    def clear_estimate(self):
        self._gmms = {}
        self._scale = {}
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
    def get_notebook_code(self, idx):
        op = GaussianMixtureOp()
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
    
        
class GaussianMixture1DViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('channel',
                                style = 'readonly'),
                           Item('by',
                                editor = TextEditor(),
                                style = 'readonly',
                                label = "Group\nBy"),
                           Item('xfacet',
                                editor=ExtendableEnumEditor(name='by',
                                                            extra_items = {"None" : ""}),
                                label = "Horizontal\nFacet"),
                           Item('yfacet',
                                editor=ExtendableEnumEditor(name='by',
                                                            extra_items = {"None" : ""}),
                                label = "Vertical\nFacet"),
                           Item('huefacet',
                                editor=ExtendableEnumEditor(name='by',
                                                            extra_items = {"None" : ""}),
                                label="Color\nFacet"),
                           label = "1D Mixture Model Default Plot",
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
class GaussianMixture1DPluginView(PluginViewMixin, GaussianMixture1DView):
    handler_factory = Callable(GaussianMixture1DViewHandler, transient = True)
    op = Instance(IOperation, fixed = True)
    subset = DelegatesTo('op', transient = True)
    by = DelegatesTo('op', status = True)
    channel = DelegatesTo('op', transient = True)
    scale = DelegatesTo('op', 'channel_scale', transient = True)
    plot_params = Instance(HistogramPlotParams, ())

    def plot_wi(self, wi):
        if wi.result:
            if self.plot_names:
                self.plot(wi.result, 
                          plot_name = self.current_plot,
                          **self.plot_params.trait_get())
            else:
                self.plot(wi.result, **self.plot_params.trait_get())
        else:
            if self.plot_names:
                self.plot(wi.previous_wi.result, 
                          plot_name = self.current_plot,
                          **self.plot_params.trait_get())
            else:
                self.plot(wi.previous_wi.result, **self.plot_params.trait_get())
        
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
        view = GaussianMixture1DView()
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
class GaussianMixture1DPlugin(Plugin, PluginHelpMixin):

    id = 'edu.mit.synbio.cytoflowgui.op_plugins.gaussian_1d'
    operation_id = 'edu.mit.synbio.cytoflowgui.operations.gaussian_1d'

    short_name = "1D Mixture Model"
    menu_group = "Gates"
    
    def get_operation(self):
        return GaussianMixture1DPluginOp()
    
    def get_icon(self):
        return ImageResource('gauss_1d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
@camel_registry.dumper(GaussianMixture1DPluginOp, 'gaussian-1d', version = 1)
def _dump(op):
    return dict(name = op.name,
                channel = op.channel,
                channel_scale = op.channel_scale,
                num_components = op.num_components,
                sigma = op.sigma,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('gaussian-1d', version = 1)
def _load(data, version):
    return GaussianMixture1DPluginOp(**data)

@camel_registry.dumper(GaussianMixture1DPluginView, 'gaussian-1d-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                xfacet = view.xfacet,
                yfacet = view.yfacet,
                huefacet = view.huefacet,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(GaussianMixture1DPluginView, 'gaussian-1d-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op)

@camel_registry.loader('gaussian-1d-view', version = any)
def _load_view(data, version):
    return GaussianMixture1DPluginView(**data)
    
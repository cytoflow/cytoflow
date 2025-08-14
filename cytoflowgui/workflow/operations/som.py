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

"""
cytoflowgui.workflow.operations.som
-----------------------------------

"""

from traits.api import (HasTraits, provides, Str, Property, observe, 
                        List, Dict, Any, Enum, Int, Float, Bool, Instance,
                        Constant, Tuple)

from cytoflow.operations.som import SOMOp, SOM1DView, SOM2DView
from cytoflow.operations.base_op_views import OpView
import cytoflow.utility as util

from ..views import IWorkflowView, WorkflowByView
from ..views.view_base import DataPlotParams, LINE_STYLES, SCATTERPLOT_MARKERS

from ..serialization import camel_registry, cytoflow_class_repr, traits_repr, dedent, traits_str
from ..subset import ISubset

from .operation_base import IWorkflowOperation, WorkflowOperation

SOMOp.__repr__ = cytoflow_class_repr

class Channel(HasTraits):
    channel = Str
    scale = util.ScaleEnum
    
    def __repr__(self):
        return traits_repr(self)
    
class SOMPlotParams(DataPlotParams):
    # Data1DPlotParams
    lim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    orientation = Enum('vertical', 'horizontal')
    
    # HistogramPlotParams
    num_bins = util.PositiveCInt(None, allow_none = True)
    histtype = Enum(['stepfilled', 'step', 'bar'])
    linestyle = Enum(LINE_STYLES)
    linewidth = util.PositiveCFloat(None, allow_none = True, allow_zero = True)
    
    # Data2DPlotParams
    xlim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))   
    ylim = Tuple(util.FloatOrNone(None), util.FloatOrNone(None))
    
    # ScatterplotPlotParams
    s = util.PositiveCFloat(2)
    marker = Enum(SCATTERPLOT_MARKERS)
    
    # shared
    alpha = util.PositiveCFloat(0.5)

    
@provides(IWorkflowView)
class SOMWorkflowView(WorkflowByView, OpView):
    id = Constant('cytoflowgui.workflow.operations.somworkflowview')

    op = Instance(IWorkflowOperation, fixed = True)
    plot_params = Instance(SOMPlotParams, ()) 
    
    def plot(self, experiment, **kwargs):
        if len(self.op.channels) == 1:
            
            kwargs.pop('xlim', None)
            kwargs.pop('ylim', None)
            kwargs.pop('s', None)
            kwargs.pop('marker', None)
            
            v = SOM1DView(op = self.op)
            v.trait_set(channel = self.op.channels[0], 
                        scale = self.op.scale[self.op.channels[0]])
            v.plot(experiment, **kwargs)
            
        elif len(self.op.channels) == 2:
            
            kwargs.pop('lim', None)
            kwargs.pop('orientation', None)
            kwargs.pop('num_bins', None)
            kwargs.pop('histtype', None)
            kwargs.pop('linestyle', None)
            kwargs.pop('linewidth', None)
            
            v = SOM2DView(op = self.op)
            v.trait_set(xchannel = self.op.channels[0], 
                        ychannel = self.op.channels[1],
                        xscale = self.op.scale[self.op.channels[0]],
                        yscale = self.op.scale[self.op.channels[1]])
            v.plot(experiment, **kwargs)
            
        else:
            raise util.CytoflowViewError(None, "Can only plot a diagnostic if there are 1 or 2 channels!")
    
    def get_notebook_code(self, idx):
        if len(self.op.channels) == 1:
            view = SOM1DView()
            plot_params = self.plot_params.clone_traits(copy = "deep")
            # reset the scatterplot traits
            plot_params.reset_traits(traits = ['xlim', 'ylim', 'alpha', 's', 
                                               'marker'])
        elif len(self.op.channels) == 2:
            view = SOM2DView()
            plot_params = self.plot_params.clone_traits(copy = "deep")
            # reset histogram traits
            plot_params.reset_traits(traits = ['lim', 'orientation', 'num_bins',
                                               'histtype', 'linestyle', 'linewidth',
                                               'density', 'alpha'])
        else:
            return ""
        
        view.copy_traits(self, view.copyable_trait_names())
        view.subset = self.subset
        plot_params_str = traits_str(plot_params)
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{idx}{plot}{plot_params})
        """
        .format(traits = traits_str(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.current_plot else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))
    
    
@provides(IWorkflowOperation)    
class SOMWorkflowOp(WorkflowOperation, SOMOp):
    # use a list of _Channel instead of separate lists/dicts of channels/scales
    channels_list = List(Channel, estimate = True)
    channels = Property(List(Str), 
                        observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    scale = Property(Dict(Str, util.ScaleEnum),
                     observe = '[channels_list.items,channels_list.items.channel,channels_list.items.scale]')
    
    # add 'estimate', 'apply' metadata
    name = Str(apply = True)
    by = List(Str, estimate = True)
    # SOM parameters
    width = Int(10, estimate = True)
    height = Int(10, estimate = True)
    distance = Enum("euclidean", "cosine", "chebyshev", "manhattan", estimate = True)
    learning_rate = Float(0.5, estimate = True)
    sigma = Float(1.0, estimate = True)
    num_iterations = Int(20, estimate = True)
    sample = util.UnitFloat(0.1, estimate = True)
    
    # consensus clustering parameters
    consensus_cluster = Bool(True, estimate = True)
    min_clusters = Int(2, estimate = True)
    max_clusters = Int(10, estimate = True)
    n_resamples = Int(100, estimate = True)
    resample_frac = Float(0.8, estimate = True)
    
    # add the 'estimate_result' metadata
    _som = Dict(Any, Instance("cytoflow.utility.minisom.MiniSom"), transient = True, estimate_result = True)
    
    # override the base class's "subset" with one that is dynamically generated /
    # updated from subset_list
    subset = Property(Str, observe = "subset_list.items.str")
    subset_list = List(ISubset, estimate = True)
    
    # bits for channels
    @observe('[channels_list:items,channels_list:items.channel,channels_list:items.scale]')
    def _channels_updated(self, event):
        self.changed = 'channels_list'
        
    def _get_channels(self):
        return [c.channel for c in self.channels_list]
    
    def _get_scale(self):
        return {c.channel : c.scale for c in self.channels_list}
    
    # bits to support the subset editor
    @observe('subset_list:items.str')
    def _on_subset_changed(self, _):
        self.changed = 'subset_list'
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    def estimate(self, experiment):
        for i, channel_i in enumerate(self.channels_list):
            for j, channel_j in enumerate(self.channels_list):
                if channel_i.channel == channel_j.channel and i != j:
                    raise util.CytoflowOpError("Channel {0} is included more than once"
                                               .format(channel_i.channel))
        
        super().estimate(experiment, subset = self.subset)
        
    def apply(self, experiment):
        if not self._som:
            raise util.CytoflowOpError(None, 'Click "Estimate"!')
        
        return super().apply(experiment)
            
    def clear_estimate(self):
        self._som = {}
        
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the k-means clustering.
         
        Returns
        -------
            IView : an IView, call `SOMWorkflowView.plot` to see the diagnostic plot.
        """
            
        return SOMWorkflowView(op = self, **kwargs)

    
    def get_notebook_code(self, idx):
        op = SOMOp()
        op.copy_traits(self, op.copyable_trait_names())
        
        op.channels = [c.channel for c in self.channels_list]
        op.scale = {c.channel : c.scale for c in self.channels_list}

        return dedent("""
        op_{idx} = {repr}
        
        op_{idx}.estimate(ex_{prev_idx}{subset})
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1,
                subset = ", subset = " + repr(self.subset) if self.subset else ""))
        

### Serialization
@camel_registry.dumper(SOMWorkflowOp, 'som', version = 1)
def _dump(op):
    return dict(name = op.name,
                channels_list = op.channels_list,
                width = op.width,
                height = op.height,
                distance = op.distance,
                learning_rate = op.learning_rate,
                sigma = op.sigma,
                num_iterations = op.num_iterations,
                sample = op.sample,
                consensus_cluster = op.consensus_cluster,
                min_clusters = op.min_clusters,
                max_clusters = op.max_clusters,
                n_resamples = op.n_resamples,
                resample_frac = op.resample_frac,
                by = op.by,
                subset_list = op.subset_list)
    
@camel_registry.loader('som', version = 1)
def _load(data, version):
    return SOMWorkflowOp(**data)

@camel_registry.dumper(SOMWorkflowView, 'som-view', version = 1)
def _dump_view(view):
    return dict(op = view.op,
                plot_params = view.plot_params,
                current_plot = view.current_plot)

@camel_registry.loader('som-view', version = any)
def _load_view(data, ver):
    return SOMWorkflowView(**data)


@camel_registry.dumper(Channel, 'som-channel', version = 1)
def _dump_channel(channel):
    return dict(channel = channel.channel,
                scale = channel.scale)
    
@camel_registry.loader('som-channel', version = 1)
def _load_channel(data, version):
    return Channel(**data)

@camel_registry.dumper(SOMPlotParams, 'som-view-params', version = 1)
def _dump_params(params):
    return dict(# BasePlotParams
                title = params.title,
                xlabel = params.xlabel,
                ylabel = params.ylabel,
                huelabel = params.huelabel,
                col_wrap = params.col_wrap,
                sns_style = params.sns_style,
                sns_context = params.sns_context,
                legend = params.legend,
                sharex = params.sharex,
                sharey = params.sharey,
                despine = params.despine,

                # DataplotParams
                min_quantile = params.min_quantile,
                max_quantile = params.max_quantile,
                
                # Data1DPlotParams
                lim = params.lim,
                orientation = params.data_orintation,
                
                # HistogramPlotParams
                num_bins = params.num_bins,
                histtype = params.histtype,
                linestyle = params.linestyle,
                linewidth = params.linewidth,
                
                # Data2DPlotParams
                xlim = params.xlim,
                ylim = params.ylim,
                
                # Scatterplot params
                s = params.s,
                marker = params.marker,
                
                # Density plot params
                gridsize = params.gridsize,
                smoothed = params.smoothed,
                smoothed_sigma = params.smoothed_sigma,
    
                # shared
                alpha = params.alpha)
    
@camel_registry.loader('som-view-params', version = any)
def _load_params(data, version):
    return SOMPlotParams(**data)

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
cytoflowgui.workflow.views.mst
---------------------------------

"""

from textwrap import dedent

from traits.api import provides, Instance, HasStrictTraits, Str, Bool, Enum, Callable

from cytoflow import MSTView
from ..serialization import camel_registry, cytoflow_class_repr, traits_str, traits_repr
from .view_base import IWorkflowView, WorkflowByView, COLORMAPS

MSTView.__repr__ = cytoflow_class_repr

class MSTPlotParams(HasStrictTraits):
    title = Str
    legendlabel = Str

    sns_style = Enum(['whitegrid', 'darkgrid', 'white', 'dark', 'ticks'])
    sns_context = Enum(['notebook', 'paper', 'poster', 'talk'])

    legend = Bool(True)
    palette = Enum([''] + list(COLORMAPS.keys()))
        
    def __repr__(self):
        return traits_repr(self)


@provides(IWorkflowView)
class MSTWorkflowView(WorkflowByView, MSTView):
    
    # callables aren't picklable, so make this one transient 
    # and send scale_by_events instead
    size_function = Callable(transient = True)
    scale_by_events = Bool(False)
    
    plot_params = Instance(MSTPlotParams, ())
    
    def plot(self, experiment, **kwargs):
        if self.scale_by_events:
            self.size_function = len
        else:
            self.size_function = None
        
        super().plot(experiment, **kwargs)
            
    def get_notebook_code(self, idx):
        view = MSTView()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)

        return dedent("""
        {repr}.plot(ex_{idx}{plot}{plot_params})
        """
        .format(repr = repr(view),
                idx = idx,
                plot = ", plot_name = " + repr(self.current_plot) if self.current_plot else "",
                plot_params = ", " + plot_params_str if plot_params_str else ""))
        
### Serialization
@camel_registry.dumper(MSTWorkflowView, 'mst', version = 1)
def _dump(view):
    return dict(statistic = view.statistic,
                locations = view.locations,
                locations_level = view.locations_level,
                locations_features = view.locations_features,
                feature = view.feature,     
                variable = view.variable,   
                style = view.style,
                scale = view.scale,     
                metric = view.metric,       
                subset_list = view.subset_list,   
                scale_by_events = view.scale_by_events,
                plot_params = view.plot_params,   
                current_plot = view.current_plot) 
    
@camel_registry.dumper(MSTPlotParams, 'mst-params', version = 1)
def _dump_params(params):
    return dict(title = params.title,
                legendlabel = params.legendlabel,
                sns_style = params.sns_style,
                sns_context = params.sns_context,
                legend = params.legend,
                palette = params.palette,
                )

@camel_registry.loader('mst', version = 1)
def _load(data, _):
    return MSTWorkflowView(**data)

@camel_registry.loader('mst-params', version = any)
def _load_params(data, _):
    return MSTPlotParams(**data)


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
cytoflowgui.workflow.views.matrix
---------------------------------

"""

from textwrap import dedent
import matplotlib.pyplot as plt

from traits.api import provides, Instance, HasStrictTraits, Str, Bool, Enum, Callable

from cytoflow import MatrixView
from ..serialization import camel_registry, cytoflow_class_repr, traits_str, traits_repr
from .view_base import IWorkflowView, WorkflowByView, COLORMAPS

MatrixView.__repr__ = cytoflow_class_repr

class MatrixPlotParams(HasStrictTraits):
    title = Str
    xlabel = Str
    ylabel = Str
    legendlabel = Str

    sns_style = Enum(['whitegrid', 'darkgrid', 'white', 'dark', 'ticks'])
    sns_context = Enum(['notebook', 'paper', 'poster', 'talk'])

    legend = Bool(True)
    palette = Enum([''] + list(COLORMAPS.keys()))
        
    def __repr__(self):
        return traits_repr(self)


@provides(IWorkflowView)
class MatrixWorkflowView(WorkflowByView, MatrixView):
    
    # callables aren't picklable, so make this one transient 
    # and send scale_by_events instead
    size_function = Callable(transient = True)
    scale_by_events = Bool(False)
    
    plot_params = Instance(MatrixPlotParams, ())
    
    def plot(self, experiment, **kwargs):
        if self.scale_by_events:
            self.size_function = len
        else:
            self.size_function = lambda _: 1.0
            
        # gets rid of the "bad gridspec" error from the layout engine
        le = plt.gcf().get_layout_engine()
        plt.gcf().set_layout_engine('none')
        
        super().plot(experiment, **kwargs)
        
        plt.gcf().set_layout_engine(le)
    
    def get_notebook_code(self, idx):
        view = MatrixView()
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
@camel_registry.dumper(MatrixWorkflowView, 'matrix', version = 1)
def _dump(view):
    return dict(statistic = view.statistic, 
                feature = view.feature,     
                variable = view.variable,   
                scale = view.scale,         
                xfacet = view.xfacet,   
                yfacet = view.yfacet,   
                subset_list = view.subset_list,   
                scale_by_events = view.scale_by_events,
                plot_params = view.plot_params,   
                current_plot = view.current_plot) 
    
@camel_registry.dumper(MatrixPlotParams, 'matrix-params', version = 1)
def _dump_params(params):
    return dict(
                title = params.title,
                xlabel = params.xlabel,
                ylabel = params.ylabel,
                legendlabel = params.legendlabel,
                sns_style = params.sns_style,
                sns_context = params.sns_context,
                legend = params.legend,
                palette = params.palette,
                )

@camel_registry.loader('matrix', version = 1)
def _load(data, _):
    return MatrixWorkflowView(**data)

@camel_registry.loader('matrix-params', version = any)
def _load_params(data, _):
    return MatrixPlotParams(**data)


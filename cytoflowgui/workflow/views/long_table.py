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
cytoflowgui.workflow.views.long_table
--------------------------------

"""
import logging
import pandas as pd
from textwrap import dedent

from traits.api import provides, Instance

from cytoflow import LongTableView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, traits_repr
from .view_base import IWorkflowView, WorkflowByView, BasePlotParams

LongTableView.__repr__ = traits_repr


@provides(IWorkflowView)
class LongTableWorkflowView(WorkflowByView, LongTableView): 
    plot_params = BasePlotParams() # this is unused -- no view, not passed to plot()
    
    # return the result for export from the GUI process
    result = Instance(pd.DataFrame, status = True)
    
    def plot(self, experiment, **kwargs):
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
        
        super().plot(experiment)
        self.result = experiment.statistics[self.statistic]
        
    def get_notebook_code(self, idx):
        view = LongTableView()
        view.copy_traits(self, view.copyable_trait_names())

        return dedent("""
        {repr}.plot(ex_{idx})
        """
        .format(repr = repr(view),
                idx = idx))

           
### Serialization

@camel_registry.dumper(LongTableWorkflowView, 'long-table-view', version = 2)
def _dump(view):
    return dict(statistic = view.statistic,
                subset_list = view.subset_list,
                current_plot = view.current_plot)
    
@camel_registry.dumper(LongTableWorkflowView, 'long-table-view', version = 1)
def _dump_v1(view):
    return dict(statistic = view.statistic,
                subset_list = view.subset_list,
                current_plot = view.current_plot)
    
@camel_registry.loader('long-table-view', version = 2)
def _load(data, version):
    return LongTableWorkflowView(**data)

@camel_registry.loader('long-table-view', version = 1)
def _load_v1(data, version):
    
    logging.warn("Statistics have changed substantially since you saved this "
                 ".flow file, so you'll need to reset a few things. "
                 "See the FAQ in the online documentation for details.")
    
    data['statistic'] = tuple(data['statistic'])[0]
    return LongTableWorkflowView(**data)

#!/usr/bin/env python3.8
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

"""
Table
-----

Make a table out of a statistic.  The table can then be exported.

.. object:: Statistic

    Which statistic to view.
    
.. object:: Rows

    Which variable to use for the rows

.. object:: Subrows

    Which variable to use for subrows.
    
.. object:: Columns

    Which variable to use for the columns.
    
.. object:: Subcolumns

    Which variable to use for the subcolumns.
    
.. object:: Export

    Export the table to a CSV file.

    
.. plot::
        
    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()
    
    ex2 = flow.ThresholdOp(name = 'Threshold',
                           channel = 'Y2-A',
                           threshold = 2000).apply(ex)
    

    ex3 = flow.ChannelStatisticOp(name = "ByDox",
                                  channel = "Y2-A",
                                  by = ['Dox', 'Threshold'],
                                  function = len).apply(ex2) 

    flow.TableView(statistic = ("ByDox", "len"),
                   row_facet = "Dox",
                   column_facet = "Threshold").plot(ex3)    

"""

import pandas as pd
from textwrap import dedent

from traits.api import provides, Instance

from cytoflow import TableView
import cytoflow.utility as util

from cytoflowgui.workflow.serialization import camel_registry, traits_repr
from .view_base import IWorkflowView, WorkflowByView, BasePlotParams

TableView.__repr__ = traits_repr


@provides(IWorkflowView)
class TableWorkflowView(WorkflowByView, TableView): 
    plot_params = BasePlotParams() # this is unused -- no view, not passed to plot()
    
    # return the result for export from the GUI process
    result = Instance(pd.Series, status = True)
    
    def plot(self, experiment, **kwargs):
        if experiment is None:
            raise util.CytoflowViewError("No experiment specified")
        
        super().plot(experiment)
        self.result = experiment.statistics[self.statistic]
        
    def get_notebook_code(self, idx):
        view = TableView()
        view.copy_traits(self, view.copyable_trait_names())

        return dedent("""
        {repr}.plot(ex_{idx})
        """
        .format(repr = repr(view),
                idx = idx))

           
### Serialization

@camel_registry.dumper(TableWorkflowView, 'table-view', version = 1)
def _dump(view):
    return dict(statistic = view.statistic,
                row_facet = view.row_facet,
                subrow_facet = view.subrow_facet,
                column_facet = view.column_facet,
                subcolumn_facet = view.subcolumn_facet,
                subset_list = view.subset_list,
                current_plot = view.current_plot)
    
@camel_registry.loader('table-view', version = 1)
def _load(data, version):
    data['statistic'] = tuple(data['statistic'])
    return TableWorkflowView(**data)

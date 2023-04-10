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
cytoflow.operations.bulk_condition_op
-----------------------------

Adds a set of conditions from a pandas.DataFrames to an `Experiment`. `bulk_condition_op` has one class:

`ExternalLabelOp` -- Adds a set of conditions, given corresponding values in a pandas.DataFrame, to an `Experiment`.

"""

import os
from traits.api import (HasStrictTraits, Str, Instance, 
                        Bool, observe, provides, List,
                        Constant)
    
import pandas as pd

import matplotlib.pyplot as plt

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class BulkConditionOp(HasStrictTraits):
    """
    Applies given conditions to an cytometry experiment.
    
    Attributes
    ----------
    conditions_csv_path : Str
        The path to a CSV file containing the labels.
        
    conditions : pd.DataFrame
        The labels to apply.

    combine_order : List(Str)
        A list of conditions to combine in the given order. Results in a new condition with the name `combined_conditions_name`.
        The new condition will be the name of last condition in `combine_order` that is true for a given measurement.
    
    combined_conditions_name : Str (default = "combined_conditions")
        The name of the new condition created by combining the conditions in `combine_order`.
    
    combined_condition_default : Str (default = "No Condition")
        The default value of an measurement for the new condition created by combining the conditions in `combine_order`.
        This value will be applied if none of combine_order conditions are true for a given measurement.
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.bulk_condition')
    friendly_id = Constant("bulk condition")
    
    conditions_df = Instance(pd.DataFrame, args=(), copy = "ref")
    conditions_csv_path = Str
    combine_order = List(Str)
    combined_conditions_name = Str("combined_conditions")
    combined_condition_default = Str("No Condition")
    
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : `Experiment`
            the `Experiment` to which this operation is applied
            
        Returns
        -------
        Experiment
            a new `Experiment`, the same as the old experiment but with 
            a new columns of type ``bool`` with the same name in the given dataframe.
            The new condition is ``True`` if it's true in the given dataframe.
            If 'combine_order' contains elements the resulting experiment will also have a new condition 
            with the name `combined_conditions_name` that is the name of the last condition 
            in `combine_order` that is true for a given measurement.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        if self.conditions_csv_path is not None and self.conditions_csv_path != "":
            if not os.path.exists(self.conditions_csv_path):
                raise util.CytoflowOpError('conditions_csv_path', "File {0} does not exist".format(self.conditions_csv_path))
            
            self.conditions_df = pd.read_csv(self.conditions_csv_path)
        
        # make sure labels got set!
        if self.conditions_df is None or self.conditions_df.empty:
            raise util.CytoflowOpError('conditions_df', 
                                       "You have to set the conditions_df "
                                       "before applying them!")
        
        if not isinstance(self.conditions_df, pd.DataFrame):
            raise util.CytoflowOpError('conditions_df', 
                                       "conditions_df is not a pandas.DataFrame")
            
        
        # make sure old_experiment doesn't already have a column named self.name
        new_cols = set(self.conditions_df.columns)
        old_cols = set(experiment.data.columns)
        intersection = new_cols.intersection(old_cols)
        if(len(intersection) > 0):
            raise util.CytoflowOpError("one or more columns in conditions_df already exists in the experiment",
                                       "Experiment already contains column {0}"
                                       .format(list(intersection).join(", ")))

        new_experiment = experiment.clone(deep = False)
        for col in self.conditions_df.columns:
            new_experiment.add_condition(col, "bool", self.conditions_df[col])

        if self.combine_order is not None and len(self.combine_order) > 0:
            #combine_order given
            if len(self.combine_order) != len(set(self.combine_order)):
                raise util.CytoflowOpError("combine_order", "combine_order contains duplicates")
            
            set_diff = set(self.combine_order).difference(set(new_experiment.data.columns))
            if len(set_diff) > 0:
                raise util.CytoflowOpError("combine_order", "combine_order contains condition names that are not in the experiment: {0}".format(set_diff))


            def get_combined_condition(row):
                result = self.combined_condition_default
                for con_name in self.combine_order:
                    if row[con_name] == True:
                        result = con_name
                return result
        
            new_experiment.add_condition(self.combined_conditions_name, "string", new_experiment.data.apply(get_combined_condition, axis = 1))
        
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment

        
if __name__ == '__main__':
    import cytoflow as flow
    
    tube1 = flow.Tube(file = './cytoflow/tests/data/vie14/494.fcs')
    ex = flow.ImportOp(tubes = [tube1]).apply()

    conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
    
    bulkconditions = BulkConditionOp(conditions_df = conditions_df, combine_order = ["syto", "singlets", "intact","cd19", "blast"])

    ex2 = bulkconditions.apply(ex)

    print(ex2.channels)
    print(ex2.conditions)
    print(ex2["combined_conditions"])

    scatter_plot = flow.ScatterplotView(xchannel = 'CD19', ychannel = 'SSC-A', xscale = 'logicle')
    scatter_plot.huefacet = "combined_conditions"
    scatter_plot.plot(ex2)
    
    plt.show()

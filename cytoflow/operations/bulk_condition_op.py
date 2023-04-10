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
cytoflow.operations.external_label
-----------------------------

Adds a set of conditions from pandas.DataFrames to an `Experiment`. `external_label` has one class:

`ExternalLabelOp` -- Adds a set of conditions, given corresponding values in a pandas.DataFrame, to an `Experiment`.

"""

import os
from traits.api import (HasStrictTraits, Float, Str, Instance, 
                        Bool, observe, provides, Any, Dict,
                        Constant)
    
import pandas as pd

import matplotlib.pyplot as plt

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class BulkConditionOp(HasStrictTraits):
    """
    Applies external conditions to an cytometry experiment.
    
    Attributes
    ----------
    conditions_csv_path : Str
        The path to a CSV file containing the labels.
        
    conditions : pd.DataFrame
        The labels to apply.
        
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.bulk_condition')
    friendly_id = Constant("bulk condition")
    
    conditions_df = Instance(pd.DataFrame, args=(), copy = "ref")
    conditions_csv_path = Str
    
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
            a new columns of type ``bool`` with the same name as the operation 
            `name`.  The new condition is ``True`` if the event's 
            measurement in `channel` is greater than `threshold`;
            it is ``False`` otherwise.
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
        
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment

        
if __name__ == '__main__':
    import cytoflow as flow
    
    tube1 = flow.Tube(file = './cytoflow/tests/data/vie14/494.fcs')
    ex = flow.ImportOp(tubes = [tube1]).apply()

    conditions_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
    
    bulkconditions = BulkConditionOp(conditions_df = conditions_df)

    ex2 = bulkconditions.apply(ex)

    print(ex2.channels)
    print(ex2.conditions)

    scatter_plot = flow.ScatterplotView(xchannel = 'CD19', ychannel = 'SSC-A', xscale = 'logicle')
    scatter_plot.huefacet = "blast"
    scatter_plot.plot(ex2)
    
    plt.show()

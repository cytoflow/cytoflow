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
class ExternalLabelOp(HasStrictTraits):
    """
    Applies external labels as conditions to an cytometry experiment.
    
    Attributes
    ----------
    labels_csv_path : Str
        The path to a CSV file containing the labels.
        
    labels : pd.DataFrame
        The labels to apply.
        
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.external_label')
    friendly_id = Constant("external label")
    
    labels = Instance(pd.DataFrame, args=(), copy = "ref")
    labels_csv_path = Str
    
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
        
        if self.labels_csv_path is not None and self.labels_csv_path != "":
            if not os.path.exists(self.labels_csv_path):
                raise util.CytoflowOpError('labels_csv_path', "File {0} does not exist".format(self.labels_csv_path))
            
            self.labels = pd.read_csv(self.labels_csv_path)
        
        # make sure labels got set!
        if self.labels is None or self.labels.empty:
            raise util.CytoflowOpError('labels', 
                                       "You have to set the labels "
                                       "before applying them!")
        
        if not isinstance(self.labels, pd.DataFrame):
            raise util.CytoflowOpError('labels', 
                                       "labels is not a pandas.DataFrame")
            
        
        # make sure old_experiment doesn't already have a column named self.name
        new_cols = set(self.labels.columns)
        old_cols = set(experiment.data.columns)
        intersection = new_cols.intersection(old_cols)
        if(len(intersection) > 0):
            raise util.CytoflowOpError("one or more columns in labels already exists in the experiment",
                                       "Experiment already contains column {0}"
                                       .format(list(intersection).join(", ")))

        new_experiment = experiment.clone(deep = False)
        for col in self.labels.columns:
            new_experiment.add_condition(col, "bool", self.labels[col])
        
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment

        
if __name__ == '__main__':
    import cytoflow as flow
    
    tube1 = flow.Tube(file = './cytoflow/tests/data/vie14/494.fcs')
    ex = flow.ImportOp(tubes = [tube1]).apply()

    labels_df = pd.read_csv('./cytoflow/tests/data/vie14/494_labels.csv')
    
    labels = ExternalLabelOp(labels = labels_df)

    ex2 = labels.apply(ex)

    print(ex2.channels)
    print(ex2.conditions)

    scatter_plot = flow.ScatterplotView(xchannel = 'CD19', ychannel = 'SSC-A', xscale = 'logicle')
    scatter_plot.huefacet = "blast"
    scatter_plot.plot(ex2)
    
    plt.show()

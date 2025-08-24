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
cytoflow.operations.category

Convert a binary gating strategy into a categorical condition.

`CategoryOp` -- Given an ordered list of gate names and their values, create a
categorical variable with values set by gate membership. 
"""

from traits.api import HasStrictTraits, Str, provides, Dict, Constant

import pandas as pd
from pandas.api.types import CategoricalDtype

import cytoflow.utility as util
from .i_operation import IOperation


@provides(IOperation)
class CategoryOp(HasStrictTraits):
    """
    Convert a binary gating strategy into a categorical condition.
    
    Binary gating strategies are quite common while doing manual gating.
    For example, a gating strategy might be "if a monocyte is CD64-, CD19+, 
    and CD3-, then it is a B cell; if it is CD64+, it is a macrophage". 
    Analyzing these data sets is often easier if one can specify a set of
    gate memberships, for example making a categorical variable with the
    values ``B_Cell`` and ``Macrophage``.
    
    If the gating strategy is strictly hierarchical, then you can use 
    `HierarchyOp` to accomplish this easily. For more complicated situations, 
    there is `CategoryOp`. `CategoryOp` is configured with a `dict` that maps 
    query strings to categories. `pandas.DataFrame.query` is called on each 
    query string in turn; the rows from `Experiment.data` that are returned 
    are assigned the corresponding category in the new categorical condition 
    that is created. **These subsets must be mutually exclusive,** a 
    requirement which is enforced by the operation. 
    
    Any event that is in none of the subsets is set to a default value, which
    defaults to `Unknown`. 
    
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new condition in the
        experiment that's created by `apply`.
        
    subsets : Dict(Str : Str)
        The dictionary of query strings and their corresponding categories.
        
    default : Str (default = "Unknown")
        The name that unclassified events will have in the new categorical
        condition.

        
    Examples
    --------
    Make a little data set.
    
    .. plot::
        :context: close-figs
            
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/RFP_Well_A6.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
    
    Create two threshold gates, simulating a hierarchical gating scheme.
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = flow.ThresholdOp(name = 'Y2_really_high',
        ...                        channel = 'Y2-A',
        ...                        threshold = 30000).apply(ex)
        
        >>> ex3 = flow.ThresholdOp(name = 'Y2_high',
        ...                        channel = 'Y2-A',
        ...                        threshold = 300).apply(ex2)
        
    Define the hierarchical gating scheme.
    
    .. plot::
        :context: close-figs
        
        >>> ex4 = flow.CategoryOp(name = "BO",
        ...                     subsets = {"Y2_high == False" : "Low",
        ...                                "Y2_really_high == True" : "High"},
        ...                     default = "Medium").apply(ex3)
        
    Plot the new categories.
    
    .. plot::
        :context: close-figs
        
        >>> flow.ScatterplotView(xchannel = "B1-A",
        ...                      xscale = "log",
        ...                      ychannel = "Y2-A",
        ...                      yscale = "log",
        ...                      huefacet = "BO").plot(ex4)
        
    """
    id = Constant('cytoflow.operations.category')
    friendly_id = Constant("Category Gating")
    
    name = Str
    subsets = Dict(Str, Str)
    default = Str("Unknown")
    
    def apply(self, experiment):
        """
        Computes the membership for each subset and assign the new condition's
        value accordingly.
        
        Parameters
        ----------
        experiment : Experiment
            the old `Experiment` to which this operation is applied
            
        Returns
        -------
        Experiment
            a new `Experiment`, the same as ``experiment`` but with 
            a new condition of type ``category`` with the same name as the 
            operation name. The value of the condition is the hierarchy subset
            that the event was assigned to, or left to the default value 
            otherwise. 
            
        Raises
        ------
        CytoflowOpError
            if for some reason the operation can't be applied to this
            experiment. The reason is in the ``args`` attribute.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
            
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the operation's name "
                                       "before applying it!")

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       f"{self.name} is in the experiment already!")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       f"Name {self.name} can only contain letters, numbers and underscores.") 
            
        if not self.subsets:
            raise util.CytoflowOpError('subsets',
                                       "Must specify some subsets")
            
        if len(self.subsets.values()) != len(set(self.subsets.values())):
            raise util.CytoflowOpError('subsets',
                                       "Can't reuse categories!")
    
        for category in self.subsets.values():               
            if category == self.default:
                raise util.CytoflowOpError('default',
                                           f"Default category {category} can't also be used as a gate category!")
            
        categories = pd.Series(data = [self.default] * len(experiment),
                               name = self.name,
                               dtype = CategoricalDtype(categories = list(self.subsets.values()) + [self.default],
                                                        ordered = False))
        
        for query, category in self.subsets.items():
            if not query:
                raise util.CytoflowOpError('subsets',
                                           'Subset string cant be empty!')
            which = experiment.data.query(query).index
            if (categories.loc[which] != self.default).any():
                overlap_index = (categories.loc[which] != self.default).index
                overlap_categories = list(categories.loc[overlap_index].unique())
                raise util.CytoflowOpError('subsets',
                                           f"Data from subets(s) {overlap_categories} overlaps with {category}. \n"
                                           f"Subsets must be non-overlapping!")
                
            if not category:
                raise util.CytoflowOpError('subsets',
                                           'Category string cant be empty!')
            categories.loc[which] = category
            
        new_experiment = experiment.clone(deep = False)        
        new_experiment.add_condition(self.name, "category", categories)
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
            
        return new_experiment
    
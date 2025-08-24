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
cytoflow.operations.hierarchy

Convert a hierarchical gating strategy into a categorical condition.

`HierarchyOp` -- Given an ordered list of gate names and their values, create a
categorical variable with values set by gate membership. 
"""

from traits.api import HasStrictTraits, Str, provides, Any, List, Tuple, Constant

import pandas as pd
from pandas.api.types import CategoricalDtype

import cytoflow.utility as util
from .i_operation import IOperation

@provides(IOperation)
class HierarchyOp(HasStrictTraits):
    """
    Convert a hierarchical (binary) gating strategy into a categorical condition.
    
    Hierarchical gating strategies are quite common when doing manual gating.
    For example, an 8-stain panel can separate monocytes into macrophages, B cells,
    NK cells, NKT cells, T cells, DCs, and neutrophils -- but then, because these
    states are mutually exclusive, a reasonable question is "how much of each are there?"
    ``Cytoflow`` can define these gates, but because it does not have any 
    concept of nested gates, plotting and analyzing this gating strategy can be
    challenging, particularly in the GUI.
    
    `HierarchyOp` converts a list of gates into a categorical variable to
    enable straightforward analysis. For example, monocytes stained with CD64, 
    CD3 and CD19 can differentiate between macrophages and B cells. A user
    defines a `ThresholdOp` gate to separate CD64+ cells (macrophages) from the
    rest of the events, then they use a `PolygonOp` to distinguish the CD19+/CD3-
    cells (B cells) from everything else. `HierarchyOp` can take these two gates
    and create a categorical condition with the values ``Macrophages``, ``B_Cells``,
    and ``Unknown``.
    
    The operation is set up by providing a list of conditions, values for those
    conditions, and the category that condition indicates. Figuring out an 
    event's category is done by evaluating the hierarchical gates **in order.**
    For each event, the first condition/value pair is considered. If that event
    has that value, its new category is set accordingly. If not, then the next
    gate in the list is considered. If the event is a member in none of the gates,
    it receives the category listed in the `default` attribute.
    
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new condition in the
        experiment that's created by `apply`.
        
    gates : List(Tuple(Str, Any, Str))
        The ordered list of gates that implement the gating hierarchy. 
        Each three-tuple has the following format:
        
        * ``Str`` - the *name* of the gating operation. (Must be a key in
          `Experiment.conditions` and a column in `Experiment.data`)
          
        * ``Any`` - the *value* that the gate has to have to indicate membership
          in this class.
          
        * ``Str`` - the name of this class's category, to put in the new condition.
        
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
        
        >>> ex2 = flow.ThresholdOp(name = 'B1_high',
        ...                        channel = 'B1-A',
        ...                        threshold = 500).apply(ex)
        
        >>> ex3 = flow.ThresholdOp(name = 'Y2_high',
        ...                        channel = 'Y2-A',
        ...                        threshold = 300).apply(ex2)
        
    Define the hierarchical gating scheme.
    
    .. plot::
        :context: close-figs
        
        >>> ex4 = flow.HierarchyOp(name = "Cell_Type",
        ...                        gates = [("B1_high", True, "B1_high_cells"),
        ...                                 ("Y2_high", True, "Y2_high_cells")]).apply(ex3)
        
    Plot the new categories.
    
    .. plot::
        :context: close-figs
        
        >>> flow.ScatterplotView(xchannel = "B1-A",
        ...                      xscale = "log",
        ...                      ychannel = "Y2-A",
        ...                      yscale = "log",
        ...                      huefacet = "Cell_Type").plot(ex4)
        
    """
    id = Constant('cytoflow.operations.hierarchy')
    friendly_id = Constant("Hierarchical Gating")
    
    name = Str
    gates = List(Tuple(Str, Any, Str))
    default = Str("Unknown")
    
    def apply(self, experiment):
        """
        Computes the membership at each level of the hierarchy and assigns the 
        condition's value accordingly.
        
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
            
        if not self.gates:
            raise util.CytoflowOpError('gates',
                                       "Must specify some gates!") 
    
        for gate_name, gate_val, category in self.gates:
            if gate_name not in experiment.data.columns:
                raise util.CytoflowOpError('gates',
                                           f"Gate '{gate_name}' is not in the experiment.")
                
            if gate_val not in experiment.data[gate_name].values:
                raise util.CytoflowOpError('gates',
                                           f"Value '{gate_val} was not found in gate '{gate_name}'")
                
            if category == self.default:
                raise util.CytoflowOpError('default',
                                           f"Default category {category} can't also be used as a gate category!")
            
        categories = pd.Series(data = [self.default] * len(experiment),
                               name = self.name,
                               dtype = CategoricalDtype(categories = [g[2] for g in self.gates] + [self.default],
                                                        ordered = False))
        
        for gate_name, gate_val, category in self.gates:
            which = (experiment[gate_name] == gate_val) & (categories == self.default)
            categories.loc[which] = category
            
        new_experiment = experiment.clone(deep = False)        
        new_experiment.add_condition(self.name, "category", categories)
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
            
        return new_experiment
    
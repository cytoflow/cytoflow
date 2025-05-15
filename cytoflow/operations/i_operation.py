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
cytoflow.operations.i_operation
-------------------------------

`i_operation` contains just one class:

`IOperation` -- an `traits.has_traits.Interface` that all operation classes must implement.
"""

from traits.api import Interface, Constant

class IOperation(Interface):
    """
    The basic interface for an operation on cytometry data.
    
    Attributes
    ----------
    id : Str
        a unique identifier for this class. prefix: ``cytoflow.operations``
        
    friendly_id : Str
        The operation's human-readable id (like ``Threshold`` or ``K-means``).  
        Used for UI implementations.
        
    name : Str
        The name of this IOperation instance (like ``Debris_Filter``).  Useful 
        for UI implementations; sometimes used for naming gates' metadata
    """
    
    # interface traits
    id = Constant('FIXME')
    friendly_id = Constant('FIXME')
        
    def estimate(self, experiment, subset = None):
        """
        Estimate this operation's parameters from some data.
        
        For operations that are data-driven (for example, a mixture model), 
        estimate the operation's parameters from an experiment.
        
        Parameters
        ----------
        experiment : `Experiment`
            the `Experiment` to use in the estimation.
        
        subset : Str (optional)
            a string passed to `pandas.DataFrame.query` to select the subset
            of data on which to run the parameter estimation.
            
        Raises
        ------
        `CytoflowOpException`
            If the operation can't be be completed because of bad op
            parameters.
        """ 
    
    def apply(self, experiment):
        """
        Apply an operation to an experiment.
        
        Parameters
        ----------
        experiment : `Experiment`
            the `Experiment` to apply this op to
                    
        Returns
        -------
        `Experiment`
            the old `Experiment` with this operation applied
                
        Raises
        ------
        `CytoflowOpException`
            If the operation can't be be completed because of bad op
            parameters.
        """
        
    def default_view(self, **kwargs):
        """
        Many operations have a "default" view.  This can either be a diagnostic
        for the operation's `estimate` method, an interactive for setting
        gates, etc.  Frequently it makes sense to link the properties of the
        view to the properties of the `IOperation`; sometimes, 
        `default_view` is the only way to get the view (ie, it's not 
        useful when it doesn't reference an `IOperation` instance.)
        
        Parameters
        ----------
        **kwargs : Dict
            The keyword args passed to the view's constructor
        
        Returns
        -------
        `IView`
            the `IView` instance
        """
        
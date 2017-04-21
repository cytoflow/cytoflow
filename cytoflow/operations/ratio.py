#!/usr/bin/env python2.7
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2016
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


'''
Created on Jan 18, 2017

@author: brian
'''

from __future__ import division, absolute_import

import numpy as np

from traits.api import (HasStrictTraits, Str, Constant, provides)

import cytoflow.utility as util
from .i_operation import IOperation

@provides(IOperation)
class RatioOp(HasStrictTraits):
    """
    Create a new "channel" from the ratio of two other channels.
    
    Attributes
    ----------
    name : Str
        The operation name.  Also becomes the name of the new channel.
        
    numerator : Str
        The channel that is the numerator of the ratio.
        
    denominator : Str
        The channel that is the denominator of the ratio.

        
    Metadata
    --------
    numerator : Str
        What was the numerator channel for the new one?
        
    denominator : Str
        What was the denominator channel for the new one?
    

    Examples
    --------
    >>> ratio_op = flow.RatioOp()
    >>> ratio_op.numerator = "FITC-A"
    >>> ex5 = ratio_op.apply(ex4)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.ratio')
    friendly_id = Constant("Ratio")
    
    name = Str
    numerator = Str
    denominator = Str
    
    def apply(self, experiment):
        """Applies the ratio operation to an experiment
        
        Parameters
        ----------
        experiment : Experiment
            the old experiment to which this op is applied
            
        Returns
        -------
            a new experiment with the new ratio channel
        """

        if not experiment:
            raise util.CytoflowOpError("No experiment specified")
        
        if self.numerator not in experiment.channels:
            raise util.CytoflowOpError("Channel {0} not in the experiment"
                                  .format(self.numerator))
            
        if self.denominator not in experiment.channels:
            raise util.CytoflowOpError("Channel {0} not in the experiment"
                                  .format(self.denominator))
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError("New channel {0} must be a valid Python identifier"
                                  .format(self.name))            
            
        if self.name in experiment.channels:
            raise util.CytoflowOpError("New channel {0} is already in the experiment"
                                  .format(self.name))

        new_experiment = experiment.clone()
        new_experiment.add_channel(self.name, 
                                   experiment[self.numerator] / experiment[self.denominator])
        new_experiment.data.replace([np.inf, -np.inf], np.nan, inplace = True)
        new_experiment.data.dropna(inplace = True)
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        new_experiment.metadata[self.name]['numerator'] = self.numerator
        new_experiment.metadata[self.name]['denominator'] = self.denominator
        return new_experiment
            
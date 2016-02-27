#!/usr/bin/env python2.7

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

from __future__ import division, absolute_import

import warnings, exceptions

import numpy as np
import pandas as pd
from traits.api import (HasStrictTraits, Str, List, Enum, Float, Constant,
                        provides)

import cytoflow.utility as util
from .i_operation import IOperation

@provides(IOperation)
class LogTransformOp(HasStrictTraits):
    """
    An operation that applies a natural log10 transformation to channels.
    
    .. note:: Deprecated
        Use the `scale` attributes to change the way data is plotted; leave
        the underlying data alone!
    
    It can be configured to mask or clip values less than some threshold.  
    The log10 transform is sometimes okay for basic visualization, but
    most analyses should be using `HlogTransformOp` or `LogicleTransformOp`. 
    
    Attributes
    ----------
    name : Str
        The name of the transformation (for UI representation; optional for
        interactive use)
        
    channels : List(Str)
        A list of the channels on which to apply the transformation
        
    mode : Enum("mask", "clip") (default = "mask")
        If `mask`, events with values <= `self.threshold` *in any channel* in
        `channels` are dropped.  If `clip`, values <= `self.threshold` are 
        transformed to `log10(self.threshold)`.
    
    threshold : Float (default = 1.0)
        The threshold for masking or truncation.
        
    Examples
    --------
    >>> tlog = flow.LogTransformOp()
    >>> tlog.channels =["V2-A", "Y2-A", "B1-A"]
    >>> ex2 = tlog.apply(ex)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.log')
    friendly_id = Constant("Log10")

    name = Str()
    channels = List(Str)
    mode = Enum("mask", "truncate")
    threshold = Float(1.0)
    
    def __init__(self, **kwargs):
        warnings.warn("Transforming data with LogTransformOp is deprecated; "
                      "rescale the data with the 'log' scale instead.",
                      exceptions.DeprecationWarning)
        super(LogTransformOp, self).__init__(**kwargs)
    
    def apply(self, experiment):
        """Applies the log10 transform to channels in an experiment.
        
        Parameters
        ----------
        old_experiment : Experiment
            The Experiment on which to apply this transformation.
            
        Returns
        -------
        Experiment
            A new Experiment, identical to old_experiment except for the
            transformed channels.
        """
        
        if not experiment:
            raise util.CytoflowOpError("No experiment specified")

        if not set(self.channels).issubset(set(experiment.channels)):
            raise util.CytoflowOpError("The op channels aren't in the experiment")
        
        if self.threshold <= 0:
            raise util.CytoflowOpError("op.threshold must be > 0")
        
        new_experiment = experiment.clone()
        
        data = new_experiment.data
        
        if self.mode == "mask":
            gt = pd.Series([True] * len(data.index))
        
            for channel in self.channels:
                gt = np.logical_and(gt, data[channel] > self.threshold)        

            data = data.loc[gt]
            data.reset_index(inplace = True, drop = True)
            
        new_experiment.data = data
        
        log_fwd = lambda x, t = self.threshold: \
            np.where(x <= t, np.log10(t), np.log10(x))
        
        log_rev = lambda x: 10**x
        
        for channel in self.channels:
            new_experiment[channel] = log_fwd(new_experiment[channel])
            
            new_experiment.metadata[channel]["xforms"].append(log_fwd)
            new_experiment.metadata[channel]["xforms_inv"].append(log_rev)
            
        new_experiment.history.append(self.clone_traits())
        return new_experiment

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

import math, warnings, exceptions

from traits.api import (HasStrictTraits, provides, Str, List, Float, Dict,
                        Constant)

import numpy as np

import cytoflow.utility as util
from cytoflow.utility.logicle_ext.Logicle import Logicle

from .i_operation import IOperation

@provides(IOperation)
class LogicleTransformOp(HasStrictTraits):
    """
    An implementation of the Logicle scaling method.
    
    .. note:: Deprecated
        Use the `scale` attributes to change the way data is plotted; leave
        the underlying data alone!
    
    This scaling method implements a "linear-like" region around 0, and a
    "log-like" region for large values, with a very smooth transition between
    them.  It's particularly good for compensated data, and data where you have
    "negative" events (events with a fluorescence of ~0.)
    
    If you don't have any data around 0, you might be better of with a more
    traditional log scale or a Hyperlog.
    
    The transformation has one parameter, `W`, which specifies the width of
    the "linear" range in log10 decades.  You can estimate an "optimal" value 
    with `estimate()`, or you can set it to a fixed value like 0.5.
    
    Attributes
    ----------
    name : Str 
        the name of this operation
    channels : List(Str) 
        the channels on which to apply the operation
    W : Dict(Str : float)
        for each channel, the width of the linear range, in log10 decades.  
        can estimate, or use a fixed value like 0.5.
    M : Float (default = 4.5)
        The width of the entire display, in log10 decades
    A : Dict(Str : float) 
        for each channel, additional decades of negative data to include.  
        the display usually captures all the data, so 0 is fine to start.
    r : Float
        if estimating W, the quantile of negative data used to estimate W.  
        default 0.05 is a good choice.
        
    Examples
    --------
    >>> logicle = flow.LogicleTransformOp()
    >>> logicle.channels =["V2-A", "Y2-A", "B1-A"]
    >>> logicle.estimate(ex)
    >>> ex2 = logicle.apply(ex)
        
    References
    ----------
    [1] A new "Logicle" display method avoids deceptive effects of logarithmic 
        scaling for low signals and compensated data.
        Parks DR, Roederer M, Moore WA.
        Cytometry A. 2006 Jun;69(6):541-51.
        PMID: 16604519
        http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.20258/full
        
    [2] Update for the logicle data scale including operational code 
        implementations.
        Moore WA, Parks DR.
        Cytometry A. 2012 Apr;81(4):273-7. 
        doi: 10.1002/cyto.a.22030 
        PMID: 22411901
        http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.22030/full
    """
    
    #traits
    id = Constant('edu.mit.synbio.cytoflow.operations.logicle')
    friendly_id = Constant("Logicle Transform")
    
    name = Str()
    channels = List(Str)
    
    W = Dict(Str, Float, desc="the width of the linear range, in log10 decades.")
    M = Float(4.5, desc = "the width of the display in log10 decades")
    A = Dict(Str, Float, desc = "additional decades of negative data to include.")
    r = Float(0.05, desc = "quantile to use for estimating the W parameter.")
    
    def __init__(self, **kwargs):
        warnings.warn("Transforming data with LogicleTransformOp is deprecated; "
                      "rescale the data with the 'logicle' scale instead.",
                      exceptions.DeprecationWarning)
        super(LogicleTransformOp, self).__init__(**kwargs)
    
    def estimate(self, experiment, subset = None):
        """Estimate A and W per-channel from the data (given r.)
        
        Actually, that's not quite right. Set A to 0.0; and estimate W given r.
        
        Parameters
        ----------
        experiment : Experiment
            the Experiment to use when estimating T, A and W.
        
        subset : string
            the subset of the Experiment to use; passed to 
            pandas.DataFrame.query()
        """

        if not experiment:
            raise util.CytoflowOpError("no experiment specified")
        
        if self.r <= 0 or self.r >= 1:
            raise util.CytoflowOpError("r must be between 0 and 1")
        
        if subset:
            data = experiment.query(subset)
        else:
            data = experiment.data
        
        for channel in self.channels:          
            t = experiment.metadata[channel]['range']
            self.A[channel] = 0.0
            
            # get the range by finding the rth quantile of the negative values
            neg_values = data[data[channel] < 0][channel]
            if(not neg_values.empty):
                r_value = neg_values.quantile(self.r).item()
                self.W[channel] = (self.M - math.log10(t/math.fabs(r_value)))/2
            else:
                # ... unless there aren't any negative values, in which case
                # you probably shouldn't use this transform
                self.W[channel] = 0.5
                warnings.warn( "Channel {0} doesn't have any negative data. " 
                               "Try a hlog or a log10 transform instead."
                               .format(channel),
                               util.CytoflowOpWarning)
    
    def apply(self, experiment):
        """Applies the Logicle transform to channels"""
        
        if not experiment:
            raise util.CytoflowOpError("no experiment specified")

        if not set(self.channels).issubset(set(experiment.channels)):
            raise util.CytoflowOpError("self.channels isn't a subset "
                                  "of experiment.channels")
        
        if self.M <= 0:
            raise util.CytoflowOpError("M must be > 0")

        for channel in self.channels:
            # the Logicle C++/SWIG extension is REALLY picky about it
            # being a double
            
            if experiment[channel].dtype != np.float64:
                raise util.CytoflowOpError("The dtype for channel {0} MUST be "
                                      "np.float64.  Please submit a bug report."
                                      .format(channel))
            
            if not channel in self.W: 
                raise util.CytoflowOpError("W wasn't set for channel {0}"
                                      .format(channel))
                
            if self.W[channel] <= 0:
                raise util.CytoflowOpError("W for channel {0} must be > 0"
                                      .format(channel))
            
            if not channel in self.A:
                raise util.CytoflowOpError("A wasn't set for channel {0}"
                                      .format(channel))
                
            if self.A[channel] < 0:
                raise util.CytoflowOpError("A for channel {0} must be >= 0"
                                      .format(channel))
        
        new_experiment = experiment.clone()
        
        for channel in self.channels:
            
            el = Logicle.Logicle(new_experiment.metadata[channel]['range'], 
                                 self.W[channel], 
                                 self.M,
                                 self.A[channel])
            
            logicle_fwd = lambda x: x.apply(el.scale)
            logicle_rev = lambda x: x.apply(el.inverse)
            
            new_experiment[channel] = logicle_fwd(new_experiment[channel])
            new_experiment.metadata[channel]["xforms"].append(logicle_fwd)
            new_experiment.metadata[channel]["xforms_inv"].append(logicle_rev)

        new_experiment.history.append(self.clone_traits())            
        return new_experiment

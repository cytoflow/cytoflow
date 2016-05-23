'''
Created on Feb 21, 2016

@author: brian
'''

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

import math, sys
from warnings import warn
import logging

from traits.api import HasTraits, Float, Property, Instance, Str, \
                       cached_property, Undefined, provides, Constant, Dict
                       
import numpy as np
import pandas as pd

import matplotlib.scale
from matplotlib import transforms
from matplotlib.ticker import NullFormatter, LogFormatterMathtext
from matplotlib.ticker import Locator

from .scale import IScale, register_scale
from .logicle_ext.Logicle import Logicle
from .cytoflow_errors import CytoflowError, CytoflowWarning

@provides(IScale)
class LogicleScale(HasTraits):
    """
    A scale that transforms the data using the `logicle` function.
    
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
    range : Float
        the input range of the channel.  no default!
    W : Float (default = 0.5)
        for each channel, the width of the linear range, in log10 decades.  
        can estimate, or use a fixed value like 0.5.
    M : Float (default = 4.5)
        The width of the entire display, in log10 decades
    A : Float (default = 0.0)
        for each channel, additional decades of negative data to include.  
        the display usually captures all the data, so 0 is fine to start.
    
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

    id = Constant("edu.mit.synbio.cytoflow.utility.logicle_scale")        
    name = "logicle"
    
    experiment = Instance("cytoflow.Experiment")
    channel = Str

    range = Property(Float, depends_on = "[experiment, channel]")
    W = Property(Float, depends_on = "[experiment, channel, r]")
    M = Float(4.5, desc = "the width of the display in log10 decades")
    A = Float(0.0, desc = "additional decades of negative data to include.")
    r = Float(0.05, desc = "quantile to use for estimating the W parameter.")
    
    logicle = Property(Instance(Logicle), depends_on = "[range, W, M, A]")

    mpl_params = Property(Dict, depends_on = "logicle")

    def __call__(self, data):
        """
        Transforms `data` using this scale.
        
        Careful!  May return `NaN` if the scale domain doesn't match the data 
        (ie, applying a log10 scale to negative numbers.)
        """
        
        logicle_min = self.logicle.inverse(0.0)
        logicle_max = self.logicle.inverse(1.0 - sys.float_info.epsilon) 
        def clip_scale(x):
            return 0.0 if x <= logicle_min else \
                   1.0 if x >= logicle_max else \
                   self.logicle.scale(x)
                          
        scale_fn = np.vectorize(clip_scale)

        return scale_fn(data)
        
    def inverse(self, data):
        """
        Transforms 'data' using the inverse of this scale.
        """
        inverse = np.vectorize(self.logicle.inverse)
        return inverse(pd.Series(data).clip(0, 1.0 - sys.float_info.epsilon))
    
    @cached_property
    def _get_range(self):
        if self.experiment and self.channel:
            return self.experiment.metadata[self.channel]["range"]
        else:
            return Undefined
        
    @cached_property
    def _get_W(self):
        if not (self.experiment and self.channel):
            return Undefined
        
        data = self.experiment[self.channel]
        
        if self.r <= 0 or self.r >= 1:
            raise CytoflowError("r must be between 0 and 1")
        
        # get the range by finding the rth quantile of the negative values
        neg_values = data[data < 0]
        if(not neg_values.empty):
            r_value = neg_values.quantile(self.r).item()
            return (self.M - math.log10(self.range/math.fabs(r_value)))/2
        else:
            # ... unless there aren't any negative values, in which case
            # you probably shouldn't use this transform
            warn("Channel {0} doesn't have any negative data. " 
                 "Try a log transform instead."
                 .format(self.channel),
                 CytoflowWarning)
            return 0.5
        
    @cached_property
    def _get_logicle(self):
        if self.range is Undefined or self.W is Undefined:
            return Undefined
        
        if self.range <= 0:
            raise CytoflowError("Logicle range must be > 0")
        
        if self.W < 0:
            raise CytoflowError("Logicle param W must be >= 0")
        
        if self.M <= 0:
            raise CytoflowError("Logicle param M must be > 0")
        
        if (2 * self.W > self.M):
            raise CytoflowError("Logicle param W is too large; it must be "
                                "less than half of param M.")
        
        if (-self.A > self.W or self.A + self.W > self.M - self.W):
            raise CytoflowError("Logicle param A is too large.")
        
         
        return Logicle(self.range, self.W, self.M, self.A)
    
    @cached_property
    def _get_mpl_params(self):
        return {"logicle" : self.logicle}
    
register_scale(LogicleScale)
        
class MatplotlibLogicleScale(HasTraits, matplotlib.scale.ScaleBase):   
    name = "logicle"
    logicle = Instance(Logicle)

    def __init__(self, axis, **kwargs):
        HasTraits.__init__(self, **kwargs)
    
    def get_transform(self):
        """
        Returns the matplotlib.transform instance that does the actual 
        transformation
        """
        if not self.logicle:
            # this usually happens when someone tries to say 
            # plt.xscale("logicle").  you can, in fact, do that, but
            # you have to get a parameterized instance of the transform
            # from utility.scale.scale_factory().
            
            raise CytoflowError("You can't set a 'logicle' scale directly.")
        
        return MatplotlibLogicleScale.LogicleTransform(logicle = self.logicle)
    
    def set_default_locators_and_formatters(self, axis):
        """
        Set the locators and formatters to reasonable defaults for
        linear scaling.
        """
        axis.set_major_locator(LogicleMajorLocator())
        #axis.set_major_formatter(ScalarFormatter())
        axis.set_major_formatter(LogFormatterMathtext(10))
        axis.set_minor_locator(LogicleMinorLocator())
        axis.set_minor_formatter(NullFormatter())        

    class LogicleTransform(HasTraits, transforms.Transform):
        # There are two value members that must be defined.
        # ``input_dims`` and ``output_dims`` specify number of input
        # dimensions and output dimensions to the transformation.
        # These are used by the transformation framework to do some
        # error checking and prevent incompatible transformations from
        # being connected together.  When defining transforms for a
        # scale, which are, by definition, separable and have only one
        # dimension, these members should always be set to 1.
        input_dims = 1
        output_dims = 1
        is_separable = True
        has_inverse = True
        
        # the Logicle instance
        logicle = Instance(Logicle)
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)
        
        def transform_non_affine(self, values):
            scale = np.vectorize(self.logicle.scale)
            return scale(values)

        def inverted(self):
            return MatplotlibLogicleScale.InvertedLogicleTransform(logicle = self.logicle)
        
    class InvertedLogicleTransform(HasTraits, transforms.Transform):
        input_dims = 1
        output_dims = 1
        is_separable = True
        has_inverse = True
     
        # the Logicle instance
        logicle = Instance(Logicle)
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)
        
        def transform_non_affine(self, values):
            inverse = np.vectorize(self.logicle.inverse)
            return inverse(values)
        
        def inverted(self):
            return MatplotlibLogicleScale.LogicleTransform(logicle = self.logicle)
        
        
class LogicleMajorLocator(Locator):
    """
    Determine the tick locations for logicle axes.
    Based on matplotlib.LogLocator
    """

    def set_params(self):
        """Empty"""
        pass

    def __call__(self):
        'Return the locations of the ticks'
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)

    def tick_values(self, vmin, vmax):
        'Every decade, including 0 and negative'
     
        vmin, vmax = self.view_limits(vmin, vmax)
        max_decade = 10 ** np.ceil(np.log10(vmax))
              
        if vmin < 0:
            min_decade = -1.0 * 10 ** np.floor(np.log10(-1.0 * vmin))
            ticks = [-1.0 * 10 ** x for x in np.arange(np.log10(-1.0 * min_decade), 1, -1)]
            ticks.append(0.0)
            ticks.extend( [10 ** x for x in np.arange(2, np.log10(max_decade), 1)])
        else:
            ticks = [0.0] if vmin == 0.0 else []
            ticks.extend( [10 ** x for x in np.arange(1, np.log10(max_decade), 1)])

        return self.raise_if_exceeds(np.asarray(ticks))

    def view_limits(self, vmin, vmax):
        'Try to choose the view limits intelligently'

        if vmax < vmin:
            vmin, vmax = vmax, vmin

        # get the nearest tenth-decade that contains the data
        
        if vmax > 0:
            logs = np.ceil(np.log10(vmax))
            vmax = np.ceil(vmax / (10 ** (logs - 1))) * (10 ** (logs - 1))             
        else: 
            vmax = 100  

        if vmin >= 0:
            vmin = 0
        else: 
            logs = np.ceil(np.log10(-1.0 * vmin))
            vmin = np.floor(vmin / (10 ** (logs - 1))) * (10 ** (logs - 1))

        return transforms.nonsingular(vmin, vmax)
    
class LogicleMinorLocator(Locator):
    """
    Determine the tick locations for logicle axes.
    Based on matplotlib.LogLocator
    """

    def set_params(self):
        """Empty"""
        pass

    def __call__(self):
        'Return the locations of the ticks'
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)

    def tick_values(self, vmin, vmax):
        'Every tenth decade, including 0 and negative'
        
        vmin, vmax = self.view_limits(vmin, vmax)
                      
        if vmin < 0:
            lt = [np.arange(10 ** x, 10 ** (x - 1), -1.0 * (10 ** (x-1)))
                  for x in np.arange(np.ceil(np.log10(-1.0 * vmin)), 1, -1)]
            
            # flatten and take the negative
            lt = [-1.0 * item for sublist in lt for item in sublist]
            
            # whoops! missed an endpoint
            lt.extend([-10.0])

            gt = [np.arange(10 ** x, 10 ** (x + 1), 10 ** x)
                  for x in np.arange(1, np.log10(vmax))]
            
            # flatten
            gt = [item for sublist in gt for item in sublist]
            
            #print gt
            
            ticks = lt
            ticks.extend(gt)
        else:
            vmin = max((vmin, 1))
            ticks = [np.arange(10 ** x, 10 ** (x + 1), 10 ** x)
                     for x in np.arange(np.log10(vmin), np.log10(vmax))]
            ticks = [item for sublist in ticks for item in sublist]

        return self.raise_if_exceeds(np.asarray(ticks))
    
matplotlib.scale.register_scale(MatplotlibLogicleScale)
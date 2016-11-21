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

from traits.api import HasStrictTraits, HasTraits, Float, Property, Instance, Str, \
                       cached_property, Undefined, provides, Constant, Dict, \
                       Tuple
                       
import numpy as np
import pandas as pd

import matplotlib.scale
from matplotlib import transforms
from matplotlib.ticker import NullFormatter, LogFormatterMathtext
from matplotlib.ticker import Locator

from .scale import IScale, register_scale
from .logicle_ext.Logicle import FastLogicle
from .cytoflow_errors import CytoflowError, CytoflowWarning

@provides(IScale)
class HlogScale(HasStrictTraits):
    """
    A scale that transforms the data using the `hyperlog` function.
    
    This scaling method implements a "linear-like" region around 0, and a
    "log-like" region for large values, with a smooth transition between
    them.
    
    The transformation has one parameter, `b`, which specifies the location of
    the transition from linear to log-like.
    
    Attributes
    ----------
    range : Float
        the input range of the channel.  no default!
    b : Float (default = 500)
        the location of the transition from linear to log-like.
    M : Float (default = 4.5)
        The width of the entire display, in log10 decades
    A : Float (default = 0.0)
        for each channel, additional decades of negative data to include.  
        the display usually captures all the data, so 0 is fine to start.
    
    References
    ----------
    [1] Hyperlog-a flexible log-like transform for negative, zero, and positive 
        valued data.
        Bagwell CB.
        Cytometry A. 2005 Mar;64(1):34-42. 
        PMID: 15700280
        http://onlinelibrary.wiley.com/doi/10.1002/cyto.a.20114/abstract
    """    

    id = Constant("edu.mit.synbio.cytoflow.utility.hlog")        
    name = "hlog"
    
    experiment = Instance("cytoflow.Experiment")
    
    # what data do we use to compute scale parameters?  set one.
    channel = Str
    condition = Str
    statistic = Tuple(Str, Str)
    
    quantiles = Tuple((0.001, 0.999))
    range_min = Property(Float)
    range_max = Property(Float)

    range = Property(Float, depends_on = "[experiment, channel]")
    b = Float(500, desc = "location of the log transition")
    
    mpl_params = Property(Dict, depends_on = "logicle")

    def __call__(self, data):
        """
        Transforms `data` using this scale.
        
        Careful!  May return `NaN` if the scale domain doesn't match the data 
        (ie, applying a log10 scale to negative numbers.)
        """
        
        f = _make_hlog_numeric(self.b, 1.0, self.range)
        
        hlog_min = hlog_inv(0.0, self.b, 1.0, self.range)
        hlog_max = hlog_inv(1.0 - sys.float_info.epsilon , self.b, 1.0, self.range)

        if isinstance(data, pd.Series):            
            data = data.clip(hlog_min, hlog_max)
            return data.apply(f)
        elif isinstance(data, np.ndarray):
            data = np.clip(data, hlog_min, hlog_max)
            return f(data)
        elif isinstance(data, float):
            data = max(min(data, hlog_max), hlog_min)
            return f(data)
        else:
            raise CytoflowError("Unknown data type in HlogScale.__call__")

        
    def inverse(self, data):
        """
        Transforms 'data' using the inverse of this scale.
        """
        
        f_inv = lambda y, b = self.b, d = self.range: hlog_inv(y, b, 1.0, d)
        
        if isinstance(data, pd.Series):            
            data = data.clip(0, 1.0 - sys.float_info.epsilon)
            return data.apply(f_inv)
        elif isinstance(data, np.ndarray):
            data = np.clip(data, 0, 1.0 - sys.float_info.epsilon)
            inverse = np.vectorize(f_inv)
            return inverse(data)
        elif isinstance(data, float):
            data = max(min(data, 1.0 - sys.float_info.epsilon), 0.0)
            return f_inv(data)
        else:
            raise CytoflowError("Unknown data type in HlogScale.inverse")
    
    @cached_property
    def _get_range(self):
        if self.experiment:
            if self.channel and self.channel in self.experiment.channels:
                if "range" in self.experiment.metadata[self.channel]:
                    return self.experiment.metadata[self.channel]["range"]
                else:
                    return self.experiment.data[self.channel].max()
            elif self.condition and self.condition in self.experiment.conditions:
                return self.experiment.data[self.condition].max()
            elif self.statistic and self.statistic in self.experiment.statistics:
                return self.experiment.statistics[self.statistic].max()
            else:
                return Undefined
        else:
            return Undefined
        
    def _get_range_min(self):
        if self.experiment:
            if self.channel and self.channel in self.experiment.channels:
                return self.experiment[self.channel].quantile(self.quantiles[0])
            elif self.condition and self.condition in self.experiment.conditions:
                return self.experiment.data[self.condition].min()
            elif self.statistic and self.statistic in self.experiment.statistics:
                return self.experiment.statistics[self.statistic].min()
            else:
                return Undefined
        else:
            return Undefined
    
    def _get_range_max(self):
        if self.experiment:
            if self.channel and self.channel in self.experiment.channels:
                return self.experiment[self.channel].quantile(self.quantiles[1])
            elif self.condition and self.condition in self.experiment.conditions:
                return self.experiment.data[self.condition].max()
            elif self.statistic and self.statistic in self.experiment.statistics:
                return self.experiment.statistics[self.statistic].max()
            else:
                return Undefined
        else:
            return Undefined

    @cached_property
    def _get_mpl_params(self):
        return {"b" : self.b,
                "range_min" : self.range_min,
                "range_max" : self.range_max}
    
register_scale(HlogScale)
        
class MatplotlibHlogScale(HasTraits, matplotlib.scale.ScaleBase):   
    name = "hlog"
    b = Float(500)
    
    range_min = Float
    range_max = Float

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
        axis.set_major_locator(LogicleMajorLocator(range_min = self.range_min, range_max = self.range_max))
        #axis.set_major_formatter(ScalarFormatter())
        axis.set_major_formatter(LogFormatterMathtext(10))
        axis.set_minor_locator(LogicleMinorLocator(range_min = self.range_min, range_max = self.range_max))
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
        logicle = Instance(FastLogicle)
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)
        
        def transform_non_affine(self, values):
            
            logicle_min = self.logicle.inverse(0.0)
            logicle_max = self.logicle.inverse(1.0 - sys.float_info.epsilon)
            if isinstance(values, pd.Series):            
                values = values.clip(logicle_min, logicle_max)
                return values.apply(self.logicle.scale)
            elif isinstance(values, np.ndarray):
                values = np.clip(values, logicle_min, logicle_max)
                scale = np.vectorize(self.logicle.scale)
                return scale(values)
            elif isinstance(values, float):
                data = max(min(values, logicle_max), logicle_min)
                return self.logicle.scale(data)
            else:
                raise CytoflowError("Unknown data type in MatplotlibLogicleScale.transform_non_affine")


        def inverted(self):
            return MatplotlibLogicleScale.InvertedLogicleTransform(logicle = self.logicle)
        
    class InvertedLogicleTransform(HasTraits, transforms.Transform):
        input_dims = 1
        output_dims = 1
        is_separable = True
        has_inverse = True
     
        # the Logicle instance
        logicle = Instance(FastLogicle)
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)
        
        def transform_non_affine(self, values):
            if isinstance(values, pd.Series):            
                values = values.clip(0, 1.0 - sys.float_info.epsilon)
                return values.apply(self.logicle.inverse)
            elif isinstance(values, np.ndarray):
                values = np.clip(values, 0, 1.0 - sys.float_info.epsilon)
                inverse = np.vectorize(self.logicle.inverse)
                return inverse(values)
            elif isinstance(values, float):
                values = max(min(values, 1.0 - sys.float_info.epsilon), 0.0)
                return self.logicle.inverse(values)
            else:
                raise CytoflowError("Unknown data type in LogicleScale.inverse")
        
        
        def inverted(self):
            return MatplotlibLogicleScale.LogicleTransform(logicle = self.logicle)
        
        
class LogicleMajorLocator(Locator):
    """
    Determine the tick locations for logicle axes.
    Based on matplotlib.LogLocator
    """
    
    def __init__(self, *args, **kwargs):
        self.range_min = kwargs.pop('range_min')
        self.range_max = kwargs.pop('range_max')
        
        super(LogicleMajorLocator, self).__init__(*args, **kwargs)

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
            
        vmin = max(vmin, self.range_min)
        vmax = min(vmax, self.range_max)

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
    
    def __init__(self, *args, **kwargs):
        self.range_min = kwargs.pop('range_min')
        self.range_max = kwargs.pop('range_max')
        
        super(LogicleMinorLocator, self).__init__(*args, **kwargs)

    def set_params(self):
        """Empty"""
        pass

    def __call__(self):
        'Return the locations of the ticks'
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)
    
    def view_limits(self, vmin, vmax):
        vmin, vmax = Locator.view_limits(self, vmin, vmax)
        vmin = max(vmin, self.range_min)
        vmax = min(vmax, self.range_max)
        
        return (vmin, vmax)

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

    
# the following functions were taken from Eugene Yurtsev's FlowCytometryTools
# http://gorelab.bitbucket.org/flowcytometrytools/
# thanks, Eugene!

import scipy.optimize

def hlog_inv(y, b, r, d):
    '''
    Inverse of base 10 hyperlog transform.
    '''
    aux = 1.*d/r *y
    s = np.sign(y)
    if s.shape: # to catch case where input is a single number
        s[s==0] = 1
    elif s==0:
        s = 1
    return s*10**(s*aux) + b*aux - s

def _make_hlog_numeric(b, r, d):
    '''
    Return a function that numerically computes the hlog transformation for given parameter values.
    '''
    hlog_obj = lambda y, x, b, r, d: hlog_inv(y, b, r, d) - x
    find_inv = np.vectorize(lambda x: scipy.optimize.brentq(hlog_obj, -2*r, 2*r, 
                                        args=(x, b, r, d)))
    return find_inv 

def hlog(x, b, r, d):
    '''
    Base 10 hyperlog transform.

    Parameters
    ----------
    x : num | num iterable
        values to be transformed.
    b : num
        Parameter controling the location of the shift 
        from linear to log transformation.
    r : num (default = 10**4)
        maximal transformed value.
    d : num (default = log10(2**18))
        log10 of maximal possible measured value.
        hlog_inv(r) = 10**d
     
    Returns
    -------
    Array of transformed values.
    '''
    hlog_fun = _make_hlog_numeric(b, r, d)
    if not hasattr(x, '__len__'): #if transforming a single number
        y = hlog_fun(x)
    else:
        n = len(x)
        if not n: #if transforming empty container
            return x
        else:
            y = hlog_fun(x)
    return y

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
Created on Feb 21, 2016

@author: brian
'''

from __future__ import division, absolute_import

from builtins import map
from traits.api import HasTraits, Float, Property, Instance, Str, \
                       cached_property, Undefined, provides, Constant, Dict, \
                       Tuple
                       
import numpy as np
import pandas as pd

import matplotlib.scale
import matplotlib.colors
from matplotlib import transforms
from matplotlib.ticker import NullFormatter, LogFormatterMathtext
from matplotlib.ticker import Locator

from .scale import IScale, ScaleMixin, register_scale
from .cytoflow_errors import CytoflowError

@provides(IScale)
class HlogScale(ScaleMixin):
    """
    A scale that transforms the data using the `hyperlog` function.
    
    This scaling method implements a "linear-like" region around 0, and a
    "log-like" region for large values, with a smooth transition between
    them.
    
    The transformation has one parameter, `b`, which specifies the location of
    the transition from linear to log-like.  The default, `500`, is good for
    18-bit scales and not good for other scales.
    
    Attributes
    ----------
    b : Float (default = 500)
        the location of the transition from linear to log-like.
    
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

    range = Property(Float)
    b = Float(200, desc = "location of the log transition")
    
    mpl_params = Property(Dict, depends_on = "[b, range, scale_min, scale_max]")

    def __call__(self, data):
        """
        Transforms `data` using this scale.
        
        Careful!  May return `NaN` if the scale domain doesn't match the data 
        (ie, applying a log10 scale to negative numbers.)
        """
        
        f = _make_hlog_numeric(self.b, 1.0, np.log10(self.range))

        if isinstance(data, pd.Series):            
            return data.apply(f)
        elif isinstance(data, np.ndarray):
            return f(data)
        elif isinstance(data, (int, float)):
            # numpy returns a 0-dim array.  wtf.
            return float(f(data))
        else:
            try:
                return list(map(f, data))
            except TypeError:
                raise CytoflowError("Unknown data type in HlogScale.__call__")

        
    def inverse(self, data):
        """
        Transforms 'data' using the inverse of this scale.
        """
        
        f_inv = lambda y, b = self.b, d = np.log10(self.range): hlog_inv(y, b, 1.0, d)
        
        if isinstance(data, pd.Series):            
            return data.apply(f_inv)
        elif isinstance(data, np.ndarray):
            inverse = np.vectorize(f_inv)
            return inverse(data)
        elif isinstance(data, float):
            return f_inv(data)
        else:
            try:
                return list(map(f_inv, data))
            except TypeError:
                raise CytoflowError("Unknown data type in HlogScale.inverse")
        
    def clip(self, data):
        return data
    
    def color_norm(self):
        if self.channel:
            vmin = self.experiment[self.channel].min()
            vmax = self.experiment[self.channel].max()
        elif self.condition:
            vmin = self.experiment[self.condition].min()
            vmax = self.experiment[self.condition].max()
        elif self.statistic:
            stat = self.experiment.statistics[self.statistic]
            try:
                vmin = min([min(x) for x in stat])
                vmax = max([max(x) for x in stat])
            except (TypeError, IndexError):
                vmin = stat.min()
                vmax = stat.max()
        else:
            raise CytoflowError("Must set one of 'channel', 'condition' "
                                "or 'statistic'.")
        
        class HlogNormalize(matplotlib.colors.Normalize):
            def __init__(self, vmin, vmax, scale):
                self._scale = scale
                matplotlib.colors.Normalize.__init__(self, vmin, vmax)
                
            def __call__(self, value, clip = None):
                # as implemented here, hlog already transforms onto a (0, 1)
                # scale
                scaled_value = self._scale(value)
                return np.ma.masked_array(scaled_value)
            
        return HlogNormalize(vmin, vmax, self)
    
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

    @cached_property
    def _get_mpl_params(self):
        return {"b" : self.b,
                "range" : self.range}
    
register_scale(HlogScale)
        
class MatplotlibHlogScale(HasTraits, matplotlib.scale.ScaleBase):   
    name = "hlog"
    
    b = Float
    range = Float

    def __init__(self, axis, **kwargs):
        HasTraits.__init__(self, **kwargs)
    
    def get_transform(self):
        """
        Returns the matplotlib.transform instance that does the actual 
        transformation
        """
        if self.b is Undefined:
            # this usually happens when someone tries to say 
            # plt.xscale("hlog").  you can, in fact, do that, but
            # you have to get a parameterized instance of the transform
            # from utility.scale.scale_factory().
            
            raise CytoflowError("You can't set a 'hlog' scale directly.")
        
        return MatplotlibHlogScale.HlogTransform(b = self.b, range = self.range)
    
    def set_default_locators_and_formatters(self, axis):
        """
        Set the locators and formatters to reasonable defaults for
        linear scaling.
        """
        axis.set_major_locator(HlogMajorLocator())
        axis.set_major_formatter(LogFormatterMathtext(10))
        axis.set_minor_locator(HlogMinorLocator())
        axis.set_minor_formatter(NullFormatter())        

    class HlogTransform(HasTraits, transforms.Transform):
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
        
        # the hyperlog params
        b = Float
        range = Float
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)
        
        def transform_non_affine(self, values):
            
            f = _make_hlog_numeric(self.b, 1.0, np.log10(self.range))

            if isinstance(values, pd.Series):            
                return values.apply(f)
            elif isinstance(values, np.ndarray):
                return f(values)
            elif isinstance(values, float):
                return f(values)
            else:
                raise CytoflowError("Unknown data type in MatplotlibHlogScale.HlogTransform.transform_non_affine")


        def inverted(self):
            return MatplotlibHlogScale.InvertedHlogTransform(b = self.b, range = self.range)
        
    class InvertedLogicleTransform(HasTraits, transforms.Transform):
        input_dims = 1
        output_dims = 1
        is_separable = True
        has_inverse = True
     
        # the hyperlog params
        b = Float
        range = Float
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)
        
        def transform_non_affine(self, values):
            
            f_inv = lambda y, b = self.b, d = np.log10(self.range): hlog_inv(y, b, 1.0, d)
            
            if isinstance(values, pd.Series):            
                return values.apply(f_inv)
            elif isinstance(values, np.ndarray):
                inverse = np.vectorize(f_inv)
                return inverse(values)
            elif isinstance(values, float):
                return f_inv(values)
            else:
                raise CytoflowError("Unknown data type in MatplotlibHlogScale.InvertedLogicleTransform.transform_non_affine")
        
        
        def inverted(self):
            return MatplotlibHlogScale.HlogTransform(b = self.b, range = self.range)
        
        
class HlogMajorLocator(Locator):
    """
    Determine the tick locations for hlog axes.
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

    def view_limits(self, data_min, data_max):
        'Try to choose the view limits intelligently'

        if data_max < data_min:
            data_min, data_max = data_max, data_min

        # get the nearest tenth-decade that contains the data
        
        if data_max > 0:
            logs = np.ceil(np.log10(data_max))
            vmax = np.ceil(data_max / (10 ** (logs - 1))) * (10 ** (logs - 1))             
        else: 
            vmax = 100  

        if data_min >= 0:
            vmin = 0
        else: 
            logs = np.ceil(np.log10(-1.0 * data_min))
            vmin = np.floor(data_min / (10 ** (logs - 1))) * (10 ** (logs - 1))

        return transforms.nonsingular(vmin, vmax)
    
class HlogMinorLocator(Locator):
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
                        
            ticks = lt
            ticks.extend(gt)
        else:
            vmin = max((vmin, 1))
            ticks = [np.arange(10 ** x, 10 ** (x + 1), 10 ** x)
                     for x in np.arange(np.log10(vmin), np.log10(vmax))]
            ticks = [item for sublist in ticks for item in sublist]

        return self.raise_if_exceeds(np.asarray(ticks))
    
matplotlib.scale.register_scale(MatplotlibHlogScale)

    
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

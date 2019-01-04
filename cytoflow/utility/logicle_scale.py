#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
cytoflow.utility.logicle_scale
------------------------------
'''

import math, sys
from warnings import warn

from traits.api import (HasStrictTraits, HasTraits, Float, Property, Instance, Str,
                        cached_property, Undefined, provides, Constant, Dict,
                        Tuple, Array)
                       
import numpy as np
import pandas as pd

import matplotlib.scale
from matplotlib import transforms
from matplotlib.ticker import NullFormatter, LogFormatterMathtext
from matplotlib.ticker import Locator
import matplotlib.colors

from .scale import IScale, register_scale
from .logicle_ext.Logicle import FastLogicle
from .util_functions import is_numeric
from .cytoflow_errors import CytoflowError, CytoflowWarning

@provides(IScale)
class LogicleScale(HasStrictTraits):
    """
    A scale that transforms the data using the `logicle` function.
    
    This scaling method implements a "linear-like" region around 0, and a
    "log-like" region for large values, with a very smooth transition between
    them.  It's particularly good for compensated data, and data where you have
    "negative" events (events with a fluorescence of ~0.)
    
    If you don't have any data around 0, you might be better of with a more
    traditional log scale.
    
    The transformation has one parameter, `W`, which specifies the width of
    the "linear" range in log10 decades.  By default, the optimal value is
    estimated from the data; but if you assign a value to `W` it will be used.
    `0.5` is usually a good start.
    
    Attributes
    ----------
    experiment : Instance(cytoflow.Experiment)
        the `cytoflow.Experiment` used to estimate the scale parameters.
        
    channel : Str
        If set, choose scale parameters from this channel in `experiment`.
        One of `channel`, `condition` or `statistic` must be set.
        
    condition : Str
        If set, choose scale parameters from this condition in `experiment`.
        One of `channel`, `condition` or `statistic` must be set.
        
    statistic : Str
        If set, choose scale parameters from this statistic in `experiment`.
        One of `channel`, `condition` or `statistic` must be set.
        
    quantiles = Tuple(Float, Float) (default = (0.001, 0.999))
        If there are a few very large or very small values, this can throw off
        matplotlib's choice of default axis ranges.  Set `quantiles` to choose
        what part of the data to consider when choosing axis ranges.
        
    W : Float (default = estimated from data)
        The width of the linear range, in log10 decades.  can estimate from data, 
        or use a fixed value like 0.5.
        
    M : Float (default = 4.5)
        The width of the log portion of the display, in log10 decades.  
        
    A : Float (default = 0.0)
        additional decades of negative data to include.  the default display 
        usually captures all the data, so 0 is fine to start.
    
    r : Float (default = 0.05)
        Quantile used to estimate `W`.
    
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
    
    # what data do we use to compute scale parameters?  set one.
    channel = Str
    condition = Str
    statistic = Tuple(Str, Str)
    error_statistic = Tuple(Str, Str)
    data = Array

    W = Property(Float, depends_on = "[experiment, channel, M, _T, r]")
    M = Float(4.5, desc = "the width of the display in log10 decades")
    A = Float(0.0, desc = "additional decades of negative data to include.")
    r = Float(0.05, desc = "quantile to use for estimating the W parameter.")

    _W = Float(Undefined)
    _T = Property(Float, depends_on = "[experiment, condition, channel]")
    _logicle = Property(Instance(FastLogicle), depends_on = "[_T, W, M, A]")
    
    def __call__(self, data):
        """
        Transforms `data` using this scale.
        
        Careful!  May return `NaN` if the scale domain doesn't match the data 
        (ie, applying a log10 scale to negative numbers.)
        """
        
        try:
            logicle_min = self._logicle.inverse(0.0)
            logicle_max = self._logicle.inverse(1.0 - sys.float_info.epsilon)
            if isinstance(data, pd.Series):            
                data = data.clip(logicle_min, logicle_max)
                return data.apply(self._logicle.scale)
            elif isinstance(data, np.ndarray):
                data = np.clip(data, logicle_min, logicle_max)
                scale = np.vectorize(self._logicle.scale)
                return scale(data)
            elif isinstance(data, float):
                data = max(min(data, logicle_max), logicle_min)
                return self._logicle.scale(data)
            elif isinstance(data, int):
                data = float(data)
                data = max(min(data, logicle_max), logicle_min)
                return self._logicle.scale(data)
            else:
                try:
                    return list(map(self._logicle.scale, data))
                except TypeError as e:
                    raise CytoflowError("Unknown data type") from e
        except ValueError as e:
            raise CytoflowError(e.strerror)

        
    def inverse(self, data):
        """
        Transforms 'data' using the inverse of this scale.
        """
        try:
            if isinstance(data, pd.Series):            
                data = data.clip(0, 1.0 - sys.float_info.epsilon)
                return data.apply(self._logicle.inverse)
            elif isinstance(data, np.ndarray):
                data = np.clip(data, 0, 1.0 - sys.float_info.epsilon)
                inverse = np.vectorize(self._logicle.inverse)
                return inverse(data)
            elif isinstance(data, float):
                data = max(min(data, 1.0 - sys.float_info.epsilon), 0.0)
                return self._logicle.inverse(data)
            elif isinstance(data, int):
                data = float(data)
                data = max(min(data, 1.0 - sys.float_info.epsilon), 0.0)
                return self._logicle.inverse(data)
            else:
                try:
                    return list(map(self._logicle.inverse, data))
                except TypeError as e:
                    raise CytoflowError("Unknown data type") from e
        except ValueError as e:
            raise CytoflowError(str(e))
        
    def clip(self, data):
        try:
            logicle_min = self._logicle.inverse(0.0)
            logicle_max = self._logicle.inverse(1.0 - sys.float_info.epsilon)
            if isinstance(data, pd.Series):            
                return data.clip(logicle_min, logicle_max)
            elif isinstance(data, np.ndarray):
                return np.clip(data, logicle_min, logicle_max)
            elif isinstance(data, float):
                return max(min(data, logicle_max), logicle_min)
            elif isinstance(data, int):
                data = float(data)
                return max(min(data, logicle_max), logicle_min)
            else:
                try:
                    return [max(min(x, logicle_max), logicle_min) for x in data]
                except TypeError as e:
                    raise CytoflowError("Unknown data type") from e
        except ValueError as e:
            raise CytoflowError(e.strerror)
        
    def norm(self, vmin = None, vmax = None):
        # it turns out that Logicle is already defined as a normalization to 
        # [0, 1].  vmin and vmax don't actually do anything here.
        class LogicleNormalize(matplotlib.colors.Normalize):
            def __init__(self, scale = None, vmin = None, vmax = None):
                self._scale = scale
                self.vmin = scale.inverse(0.0)
                self.vmax = scale.inverse(1.0 - sys.float_info.epsilon)
                
            def __call__(self, data, clip = None):
                # it turns out that Logicle is already defined as a
                # normalization to [0, 1].
                ret = self._scale(data)
                return np.ma.masked_array(ret)
            
        return LogicleNormalize(scale = self, vmin = vmin, vmax = vmax)
        
    
    @cached_property
    def _get__T(self):
        "The range of possible data values"
        if self.experiment is None:
            return Undefined
        
        if self.channel and self.channel in self.experiment.channels:
            if "range" in self.experiment.metadata[self.channel]:
                return float(self.experiment.metadata[self.channel]["range"])
            else:
                return float(self.experiment.data[self.channel].max())
        elif self.condition and self.condition in self.experiment.conditions:
            return float(self.experiment.data[self.condition].max())
        elif self.statistic in self.experiment.statistics \
             and not self.error_statistic in self.experiment.statistics:
            stat = self.experiment.statistics[self.statistic]
            assert is_numeric(stat)
            return float(stat.max())
        elif self.statistic in self.experiment.statistics and \
             self.error_statistic in self.experiment.statistics:
            stat = self.experiment.statistics[self.statistic]
            err_stat = self.experiment.statistics[self.error_statistic]
            
            try:
                err_max = max([max(x) for x in err_stat])
                return float(err_max)
            except (TypeError, IndexError):
                err_max = err_stat.max()
                stat_max = stat.max()

                return float(stat_max + err_max)
        elif self.data.size > 0:
            return float(self.data.max())
        else:
            return Undefined
        
    @cached_property
    def _get_W(self):
        if self.experiment is None:
            return Undefined
        
        if self._W is not Undefined:
            return self._W
        
        if self.channel and self.channel in self.experiment.channels:
            data = self.experiment[self.channel]
            
            if self.r <= 0 or self.r >= 1:
                raise CytoflowError("r must be between 0 and 1")
            
            # get the range by finding the rth quantile of the negative values
            neg_values = data[data < 0]
            if(not neg_values.empty):
                r_value = neg_values.quantile(self.r)
                W = (self.M - math.log10(self._T/math.fabs(r_value)))/2
                if W <= 0:
                    warn("Channel {0} doesn't have enough negative data. " 
                         "Try a log transform instead."
                         .format(self.channel),
                         CytoflowWarning)
                    return 0.5
                else:
                    return W
            else:
                # ... unless there aren't any negative values, in which case
                # you probably shouldn't use this transform
                warn("Channel {0} doesn't have any negative data. " 
                     "Try a log transform instead."
                     .format(self.channel),
                     CytoflowWarning)
                return 0.5
        else:
            return 0.5  # a reasonable default for non-channel scales
        
    def _set_W(self, value):
        self._W = value
        
    @cached_property
    def _get__logicle(self):
        if self.W is Undefined or self._T is Undefined:
            return Undefined
        
        if self._T <= 0:
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
         
        return FastLogicle(self._T, self.W, self.M, self.A)
    
    def get_mpl_params(self, ax):
        return {"logicle" : self._logicle} 
    
register_scale(LogicleScale)
        
class MatplotlibLogicleScale(HasTraits, matplotlib.scale.ScaleBase):   
    name = "logicle"
    
    logicle = Instance(FastLogicle)

    def __init__(self, axis, **kwargs):
        HasTraits.__init__(self, **kwargs)  # @UndefinedVariable
    
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
        logicle = Instance(FastLogicle)
        
        def __init__(self, **kwargs):
            transforms.Transform.__init__(self)
            HasTraits.__init__(self, **kwargs)  # @UndefinedVariable
        
        def transform_non_affine(self, values):
            
            try:        
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
                elif isinstance(values, int):
                    data = float(data)
                    data = max(min(values, logicle_max), logicle_min)
                    return self.logicle.scale(data)
                else:
                    raise CytoflowError("Unknown data type in MatplotlibLogicleScale.transform_non_affine")
                
            except ValueError as e:
                raise CytoflowError("Bad transform") from e


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
            HasTraits.__init__(self, **kwargs)  # @UndefinedVariable
        
        def transform_non_affine(self, values):
            try:
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
                elif isinstance(values, int):
                    values = float(values)
                    values = max(min(values, 1.0 - sys.float_info.epsilon), 0.0)
                    return self.logicle.inverse(values)
                else:
                    raise CytoflowError("Unknown data type in LogicleScale.inverse")
            except ValueError as e:
                raise CytoflowError("Bad transform") from e
        
        def inverted(self):
            return MatplotlibLogicleScale.LogicleTransform(logicle = self.logicle)
        
        
class LogicleMajorLocator(Locator):
    """
    Determine the tick locations for logicle axes.
    Based on matplotlib.LogLocator
    """

    def set_params(self, **kwargs):
        """Empty"""
        pass

    def __call__(self):
        'Return the locations of the ticks'
        vmin, vmax = self.axis.get_view_interval()
        return self.tick_values(vmin, vmax)

    def tick_values(self, vmin, vmax):
        'Every decade, including 0 and negative'
     
        vmin, vmax = self.view_limits(vmin, vmax)
        logicle = self.axis._scale.logicle
        
        max_decade = np.ceil(np.log10(vmax * 1.1))
        min_positive_decade = np.floor(np.log10(logicle.T()) - logicle.M())
        
        if vmin < 0:
            max_negative_decade = np.floor(np.log10(-1.0 * vmin))
            ticks = [-1.0 * 10 ** x for x in np.arange(max_negative_decade, 1, -1)]
            ticks.append(0.0)
        else:
            max_negative_decade = "N/A"
            ticks = [0.0] if vmin == 0.0 else []
            
        ticks.extend([10 ** x for x in np.arange(min_positive_decade, max_decade, 1)])
        
#         print((vmin, vmax))
#         print((max_negative_decade, min_positive_decade, max_decade))
#         print(ticks)
#         print(logicle.W())
#         ticks = [-1.0 * 10 ** x for x in np.arange(np.log10(-1.0 * min_decade), 1, -1)]
#         ticks.append(0.0)
#         ticks.extend( [10 ** x for x in np.arange(2, np.log10(max_decade), 1)])
#         print(ticks)

        return self.raise_if_exceeds(np.asarray(ticks))
        
# 
#         vmin, vmax = self.view_limits(vmin, vmax)
#         max_decade = 10 ** np.ceil(np.log10(vmax))
#               
#         if vmin < 0:
#             min_decade = -1.0 * 10 ** np.floor(np.log10(-1.0 * vmin))
#             ticks = [-1.0 * 10 ** x for x in np.arange(np.log10(-1.0 * min_decade), 1, -1)]
#             ticks.append(0.0)
#             ticks.extend( [10 ** x for x in np.arange(2, np.log10(max_decade), 1)])
#         else:
#             ticks = [0.0] if vmin == 0.0 else []
#             ticks.extend( [10 ** x for x in np.arange(1, np.log10(max_decade), 1)])
# 
#         return self.raise_if_exceeds(np.asarray(ticks))

    def view_limits(self, data_min, data_max):
        'Try to choose the view limits intelligently'
        
#         logicle = self.axis._scale.logicle
#         
#         logicle_min = logicle.inverse(0.0)
#         logicle_max = logicle.inverse(1.0 - sys.float_info.epsilon)
#         
#         return transforms.nonsingular(logicle_min, logicle_max)

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
        
        logicle = self.axis._scale.logicle
        
        max_decade = np.ceil(np.log10(vmax * 1.1))
        min_positive_decade = np.floor(np.log10(logicle.T()) - logicle.M())
        
        if vmin < 0:
            max_negative_decade = np.floor(np.log10(-1.0 * vmin))
            ticks = [-1.0 * 10 ** x for x in np.arange(max_negative_decade, 1, -0.1)]
            ticks.append(0.0)
        else:
            max_negative_decade = "N/A"
            ticks = [0.0] if vmin == 0.0 else []
            
        ticks.extend([10 ** x for x in np.arange(min_positive_decade, max_decade, 0.1)])
        
        vmin, vmax = self.view_limits(vmin, vmax)

        return self.raise_if_exceeds(np.asarray(ticks))
                      
#         if vmin < 0:
#             lt = [np.arange(10 ** x, 10 ** (x - 1), -1.0 * (10 ** (x-1)))
#                   for x in np.arange(np.ceil(np.log10(-1.0 * vmin)), 1, -1)]
#             
#             # flatten and take the negative
#             lt = [-1.0 * item for sublist in lt for item in sublist]
#             
#             # whoops! missed an endpoint
#             lt.extend([-10.0])
# 
#             gt = [np.arange(10 ** x, 10 ** (x + 1), 10 ** x)
#                   for x in np.arange(1, np.log10(vmax))]
#             
#             # flatten
#             gt = [item for sublist in gt for item in sublist]
#                         
#             ticks = lt
#             ticks.extend(gt)
#         else:
#             vmin = max((vmin, 1))
#             ticks = [np.arange(10 ** x, 10 ** (x + 1), 10 ** x)
#                      for x in np.arange(np.log10(vmin), np.log10(vmax))]
#             ticks = [item for sublist in ticks for item in sublist]
# 
#         return self.raise_if_exceeds(np.asarray(ticks))
    
#     def view_limits(self, data_min, data_max):
#         'Try to choose the view limits intelligently'
#         
#         logicle = self.axis._scale.logicle
#         
#         logicle_min = logicle.inverse(0.0)
#         logicle_max = logicle.inverse(1.0 - sys.float_info.epsilon)
#         
#         return transforms.nonsingular(logicle_min, logicle_max)
    
matplotlib.scale.register_scale(MatplotlibLogicleScale)
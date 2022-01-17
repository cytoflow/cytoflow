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
cytoflow.utility.log_scale
--------------------------

A scale that transforms data using a base-10 log.

`LogScale` -- implements `IScale`, the `cytoflow` interface for the scale.
"""

from traits.api import (Instance, Str, provides, Constant, Enum, Float, 
                        Property, Tuple, Array) 
                       
import numpy as np
import pandas as pd
import matplotlib.colors

from .scale import IScale, ScaleMixin, register_scale
from .cytoflow_errors import CytoflowError
from .util_functions import is_numeric

@provides(IScale)
class LogScale(ScaleMixin):
    id = Constant("edu.mit.synbio.cytoflow.utility.log_scale")
    name = "log"
    
    experiment = Instance("cytoflow.Experiment")
    
    # must set one of these.  they're considered in order.
    channel = Str
    condition = Str
    statistic = Tuple(Str, Str)
    error_statistic = Tuple(Str, Str)
    data = Array

    mode = Enum("mask", "clip")
    threshold = Property(Float, depends_on = "[experiment, condition, channel, statistic, error_statistic]")
    _channel_threshold = Float(0.1)

    def get_mpl_params(self, ax):
        """
        Returns a dict with the traits needed to initialize an instance of
        `matplotlib.scale.ScaleBase`
        """
        return {"nonpositive" : self.mode}
        
    def _set_threshold(self, threshold):
        self._channel_threshold = threshold
        
    def _get_threshold(self):
        if self.channel:
            return self._channel_threshold
        elif self.condition:
            cond = self.experiment[self.condition][self.experiment[self.condition] > 0]
            return cond.min()
        elif self.statistic in self.experiment.statistics \
            and not self.error_statistic in self.experiment.statistics:
            stat = self.experiment.statistics[self.statistic]
            assert is_numeric(stat)
            return stat[stat > 0].min()
        elif self.statistic in self.experiment.statistics \
            and self.error_statistic in self.experiment.statistics:
            stat = self.experiment.statistics[self.statistic]
            err_stat = self.experiment.statistics[self.error_statistic]
            stat_min = stat[stat > 0].min()
            
            try:
                err_min = min([x for x in [min(x) for x in err_stat] if x > 0])
                return err_min
                
            except (TypeError, IndexError):
                err_min = min([x for x in err_stat if stat_min - x > 0])
                return stat_min - err_min
            
        elif self.data.size > 0:
            return self.data[self.data > 0].min()
                
        
    def __call__(self, data):
        """
        Transforms `data` using this scale.
        
        Careful!  May return `NaN` if the scale domain doesn't match the data 
        (ie, applying a log10 scale to negative numbers.)
        """
        
        # this function should work with: int, float, tuple, list, pd.Series, 
        # np.ndframe.  it should return the same data type as it was passed.
        
        if isinstance(data, (int, float)):
            if self.mode == "mask":
                if data < self.threshold:
                    raise CytoflowError("data <= scale.threshold (currently: {})".format(self.threshold))
                else:
                    return np.log10(data)
            else:
                if data < self.threshold:
                    return np.log10(self.threshold)
                else:
                    return np.log10(data)
        elif isinstance(data, (list, tuple)):
            ret = [self.__call__(x) for x in data]
            if isinstance(data, tuple):
                return tuple(ret)
            else:
                return ret
        elif isinstance(data, (np.ndarray, pd.Series)):
            mask_value = np.nan if self.mode == "mask" else self.threshold
            x = pd.Series(data)
            x = x.mask(x < self.threshold, other = mask_value)
            ret = np.log10(x)
            
            if isinstance(data, pd.Series):
                return ret
            else:
                return ret.values
        else:
            raise CytoflowError("Unknown type {} passed to log_scale.__call__"
                                .format(type(data)))
                        
    def inverse(self, data):
        """
        Transforms 'data' using the inverse of this scale.
        """
        
        # this function should work with: int, float, tuple, list, pd.Series, 
        # np.ndframe
        if isinstance(data, (int, float)):
            return np.power(10, data)
        elif isinstance(data, (list, tuple)):
            ret = [np.power(10, x) for x in data]
            if isinstance(data, tuple):
                return tuple(ret)
            else:
                return ret
        elif isinstance(data, (np.ndarray, pd.Series)):
            return np.power(10, data)
        else:
            raise CytoflowError("Unknown type {} passed to log_scale.inverse"
                                .format(type(data)))
    
    def clip(self, data):
        """
        Clips data to the range of the scale function
        """
        
        if isinstance(data, pd.Series):            
            return data.clip(lower = self.threshold)
        elif isinstance(data, np.ndarray):
            return data.clip(min = self.threshold)
        elif isinstance(data, float):
            return max(data, self.threshold)
        elif isinstance(data, int):
            data = float(data)
            return max(data, self.threshold)
        else:
            try:
                return [max(x, self.threshold) for x in data]
            except TypeError as e:
                raise CytoflowError("Unknown data type in LogScale.clip") from e
            
    def norm(self, vmin = None, vmax = None):
        """
        A factory function that returns `matplotlib.colors.Normalize` instance,
        which normalizes values for a `matplotlib` color palette.
        """
        
        if vmin is not None and vmax is not None:
            pass
        elif self.channel:
            vmin = self.experiment[self.channel].min()
            vmax = self.experiment[self.channel].max()

        elif self.condition:
            vmin = self.experiment[self.condition].min()
            vmax = self.experiment[self.condition].max()
                
        elif self.statistic in self.experiment.statistics:
            stat = self.experiment.statistics[self.statistic]
            try:
                vmin = min([min(x) for x in stat])
                vmax = max([max(x) for x in stat])
            except (TypeError, IndexError):
                vmin = stat.min()
                vmax = stat.max()
                
            if self.error_statistic in self.experiment.statistics:
                err_stat = self.experiment.statistics[self.error_statistic]
                try:
                    vmin = min([min(x) for x in err_stat])
                    vmax = max([max(x) for x in err_stat])
                except (TypeError, IndexError):
                    vmin = vmin - err_stat.min()
                    vmax = vmax + err_stat.max()
        elif self.data.size > 0:
            vmin = self.data.min()
            vmax = self.data.max()
        else:
            raise CytoflowError("Must set one of 'channel', 'condition' "
                                "or 'statistic'.")
        
        return matplotlib.colors.LogNorm(vmin = self.clip(vmin), vmax = self.clip(vmax))

register_scale(LogScale)


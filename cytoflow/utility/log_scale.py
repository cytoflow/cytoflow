'''
Created on Feb 24, 2016

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

from traits.api import (HasStrictTraits, Instance, Str, Dict, provides, Constant,
                        Enum, Float, Property, Tuple) 
                       
import numpy as np
import pandas as pd

from .scale import IScale, register_scale
from .cytoflow_errors import CytoflowError


@provides(IScale)
class LogScale(HasStrictTraits):
    id = Constant("edu.mit.synbio.cytoflow.utility.log_scale")
    name = "log"
    
    experiment = Instance("cytoflow.Experiment")
    
    # must set one of these.  they're considered in order.
    channel = Str
    condition = Str
    statistic = Tuple(Str, Str)

    mode = Enum("mask", "clip")
    threshold = Property(Float, depends_on = "[experiment, condition, channel]")
    _channel_threshold = Float(0.1)

    mpl_params = Property(Dict)

    def _get_mpl_params(self):
        return {"nonposx" : self.mode, 
                "nonposy" : self.mode}
        
    def _set_threshold(self, threshold):
        self._channel_threshold = threshold
        
    def _get_threshold(self):
        if self.channel:
            return self._channel_threshold
        elif self.condition:
            return self.experiment[self.condition].min()
        elif self.statistic:
            stat = self.experiment.statistics[self.statistic]
            try:
                return min([x[0] for x in stat])
            except IndexError:
                return stat.min()
        
    def __call__(self, data):
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
            x = x.mask(lambda x: x < self.threshold, other = mask_value)
            ret = np.log10(x)
            
            if isinstance(data, pd.Series):
                return ret
            else:
                return ret.values
        else:
            raise CytoflowError("Unknown type {} passed to log_scale.__call__"
                                .format(type(data)))
                        
    def inverse(self, data):
        # this function shoujld work with: int, float, tuple, list, pd.Series, 
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
#         import pydevd; pydevd.settrace()
        if isinstance(data, pd.Series):            
            return data.clip(lower = self.threshold)
        elif isinstance(data, np.ndarray):
            return data.clip(min = self.threshold)
        elif isinstance(data, float):
            return max(data, self.threshold)
        else:
            try:
                return map(lambda x: max(data, self.threshold), data)
            except TypeError:
                raise CytoflowError("Unknown data type in LogicleScale.__call__")

register_scale(LogScale)


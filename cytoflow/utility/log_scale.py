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

from traits.api import (HasTraits, Instance, Str, Dict, provides, Constant,
                        Enum, Float, Property, cached_property, Tuple, Undefined) 
                       
import numpy as np
import pandas as pd

import matplotlib

from matplotlib.scale import LogScale as _LogScale

from matplotlib.ticker import (NullFormatter, LogFormatterMathtext)
from matplotlib.ticker import LogLocator

from .scale import IScale, register_scale
from .cytoflow_errors import CytoflowError


@provides(IScale)
class LogScale(HasTraits):
    id = Constant("edu.mit.synbio.cytoflow.utility.log_scale")
    name = "log"
    
    experiment = Instance("cytoflow.Experiment")
    channel = Str

    mode = Enum("mask", "clip")
    threshold = Float(1.0)
    quantile = Tuple(0.01, 0.999)
    
    range_min = Property(Float)
    range_max = Property(Float)

    mpl_params = Property(Dict, depends_on = "[mode, range_min, range_max]")

    @cached_property
    def _get_mpl_params(self):
        return {"nonposx" : self.mode, 
                "nonposy" : self.mode, 
                "range_min" : self.range_min,
                "range_max" : self.range_max}
        
    def _get_range_min(self):
        if self.experiment and self.channel:
            c = self.experiment[self.channel]
            return c[c > 0].quantile(self.quantile[0])
        else:
            return Undefined
    
    def _get_range_max(self):
        if self.experiment and self.channel:
            return self.experiment[self.channel].quantile(self.quantile[1])
        else:
            return Undefined
        
    def __call__(self, data):
        
        if isinstance(data, (int, float)):
            if data < self.threshold:
                raise CytoflowError("data <= scale.threshold (currently: {})".format(self.threshold))
            else:
                return np.log10(data)
            
        mask_value = np.nan if self.mode == "mask" else self.threshold
        x = pd.Series(data)
        x = x.mask(lambda x: x < self.threshold, other = mask_value)
        ret = np.log10(x)

        return (ret if isinstance(ret, pd.Series) else ret.values)
                        
    def inverse(self, data):
        return np.power(10, data)

register_scale(LogScale)
    
class RangeLogLocator(LogLocator):
    
    def __init__(self, *args, **kwargs):
        self.range_min = kwargs.pop('range_min')
        self.range_max = kwargs.pop('range_max')
        
        super(RangeLogLocator, self).__init__(*args, **kwargs)
        
    def view_limits(self, vmin, vmax):
        vmin, vmax = LogLocator.view_limits(self, vmin, vmax)
        vmin = max(vmin, self.range_min)
        vmax = min(vmax, self.range_max)
        
#         vmin = vmin * 0.5
        vmax = vmax * 2.0
        
        return (vmin, vmax)
 
class MatplotlibLogScale(_LogScale):   
     
    def __init__(self, axis, **kwargs):
        super(MatplotlibLogScale, self).__init__(axis, **kwargs)
        self._range_min = kwargs.pop('range_min', None)
        self._range_max = kwargs.pop('range_max', None)
        
    def set_default_locators_and_formatters(self, axis):
        """
        Set the locators and formatters to specialized versions for
        log scaling.
        """
        axis.set_major_locator(RangeLogLocator(self.base, range_min = self._range_min, range_max = self._range_max))
        axis.set_major_formatter(LogFormatterMathtext(self.base))
        axis.set_minor_locator(RangeLogLocator(self.base, self.subs, range_min = self._range_min, range_max = self._range_max))
        axis.set_minor_formatter(NullFormatter())

matplotlib.scale.register_scale(MatplotlibLogScale)

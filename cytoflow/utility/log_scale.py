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
                        Enum, Float, Property, cached_property) 
                       
import numpy as np

from .scale import IScale, register_scale

@provides(IScale)
class LogScale(HasTraits):
    id = Constant("edu.mit.synbio.cytoflow.utility.log_scale")
    name = "log"
    
    experiment = Instance("cytoflow.Experiment")
    channel = Str

    mode = Enum("mask", "clip")
    threshold = Float(1.0)

    mpl_params = Property(Dict, depends_on = "mode")

    @cached_property
    def _get_mpl_params(self):
        return {"nonposx" : self.mode, "nonposy" : self.mode}
        
    def __call__(self, data):
        if self.mode == "mask":
            mask = (data <= self.threshold)
            if mask.any():
                return np.log10(np.where(mask, np.nan, data))
            else:
                return np.log10(data)
        else: # mode == "clip"
            data = np.array(data, float)
            data[data <= self.threshold] = self.threshold
            return np.log10(data)

    def inverse(self, data):
        return np.power(10, data)

register_scale(LogScale)

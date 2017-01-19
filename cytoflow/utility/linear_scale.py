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

from traits.api import HasTraits, HasStrictTraits, Instance, Str, Dict, provides, Constant, Tuple
from .scale import IScale, register_scale

@provides(IScale)
class LinearScale(HasStrictTraits):
    id = Constant("edu.mit.synbio.cytoflow.utility.linear_scale")
    name = "linear"
    
    experiment = Instance("cytoflow.Experiment")
    
    # none of these are actually used
    channel = Str
    condition = Str
    statistic = Tuple(Str, Str)

    mpl_params = Dict()

    def __call__(self, data):
        return data
    
    def inverse(self, data):
        return data
    
    def clip(self, data):
        return data

register_scale(LinearScale)

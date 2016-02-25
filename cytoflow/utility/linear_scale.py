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

from __future__ import division

from traits.api import HasTraits, Instance, Str, Dict, provides, Constant, Any

#from cytoflow.experiment import Experiment
#from cytoflow.utility import IScale
from cytoflow.utility.i_scale import register_scale

#@provides(IScale)
class LinearScale(HasTraits):
    id = Constant("edu.mit.synbio.cytoflow.utility.linear_scale")
    name = "linear"
    
    experiment = Any #Instance(Experiment)
    channel = Str

    mpl_params = Dict()

    def __call__(self, data):
        return data
    
    def inverse(self, data):
        return data

register_scale(LinearScale)

#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
cytoflow.utility.linear_scale
-----------------------------
'''

import matplotlib.colors

from traits.api import Instance, Str, Dict, provides, Constant, Tuple, Array
from .scale import IScale, ScaleMixin, register_scale
from .cytoflow_errors import CytoflowError

@provides(IScale)
class LinearScale(ScaleMixin):
    """
    A scale that doesn't transform the data at all.
    """
    
    id = Constant("edu.mit.synbio.cytoflow.utility.linear_scale")
    name = "linear"
    
    experiment = Instance("cytoflow.Experiment")
    
    # none of these are actually used
    channel = Str
    condition = Str
    statistic = Tuple(Str, Str)
    error_statistic = Tuple(Str, Str)
    data = Array

    def __call__(self, data):
        return data
    
    def inverse(self, data):
        return data
    
    def clip(self, data):
        return data
    
    def norm(self, vmin = None, vmax = None):
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

        return matplotlib.colors.Normalize(vmin = vmin, vmax = vmax)
    
    def get_mpl_params(self, ax):
        return dict()
        
            

register_scale(LinearScale)

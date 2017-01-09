'''
Created on Jan 8, 2017

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

from warnings import warn

from traits.api import HasStrictTraits, Tuple, Str, provides
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import pandas as pd

import cytoflow.utility as util
from .i_view import IView

@provides(IView)
class StatisticsViewBase(HasStrictTraits):

    subset = Str
    
    def reduce_statistic(self, statistic, **variables):
        data = pd.DataFrame(index = statistic.index)
        data[statistic.name] = statistic
        
        if self.subset:
            try:
                # TODO - either sanitize column names, or check to see that
                # all conditions are valid Python variables
                data = data.query(self.subset)
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(data) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no values"
                                        .format(self.subset))
                
        names = list(data.index.names)
        
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                warn("Only one value for level {}; dropping it.".format(name),
                     util.CytoflowViewWarning)
                data.index = data.index.droplevel(name)

        names = list(data.index.names)
        
        for name, var in variables.iteritems():
            if var not in names:
                raise util.CytoflowViewError("{} {} not a statistic index; "
                                             "must be one of {}".format(name, var, names))

        return pd.Series()
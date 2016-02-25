'''
Created on Feb 25, 2016

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

from traits.api import HasTraits, Float, Instance, Property, Instance, Str, \
                       cached_property, Undefined, provides, Constant, Dict, \
                       Any
                       
import numpy as np
from warnings import warn
import math

from matplotlib import scale
from matplotlib import transforms
from matplotlib.ticker import NullFormatter, ScalarFormatter
from matplotlib.ticker import Locator

from cytoflow.utility.logicle_ext.Logicle import Logicle
from cytoflow.utility import CytoflowWarning, CytoflowError
from cytoflow.utility.i_scale import IScale, register_scale
#from cytoflow.experiment import Experiment

@provides(IScale)
class HLogScale(HasTraits):
    """Applies the Hyperlog transformation to channels.
    
    Attributes
    ----------
    name : Str
        The name of the transformation (for UI representation, optional for
        interactive use)
        
    channels : List(Str)
        A list of the channels on which to apply the transformation
        
    b: Float (default = 500)
        The point at which the transform transitions from linear to log.
        The keys are channel names and the values are transition points for
        each channel; if a channel in `channels` isn't specified here, the 
        default value of 500 is used.
    
    r: Float (default = 10**4)  
        The maximum of the transformed values.
    
    References
    ----------
    .. [1] "Hyperlog-a flexible log-like transform for negative, 
           zero, and  positive valued data."
           Bagwell CB.
           Cytometry A. 2005 Mar;64(1):34-42.
           PMID: 15700280 
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.utility.hlog_scale')
    name = "hlog"
    b = Float(500)
    r = Float(10**4)
    range = Property(Float, depends_on = "[experiment, channel]")
    
    mpl_params = Property(Dict, depends_on = "[b, r, range]")
    
    
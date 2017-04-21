#!/usr/bin/env python2.7
# coding: latin-1

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

from __future__ import absolute_import

import numbers

from traits.api import Interface, Str, Dict, Instance, Tuple

from .cytoflow_errors import CytoflowError
from .util_functions import is_numeric
from traits.has_traits import HasStrictTraits

class IScale(Interface):
    """An interface for various ways we could rescale flow data.
    
    Attributes
    ----------
    name : Str
        The name of this view (for serialization, UI, etc.)
        
    experiment : Instance(Experiment)
        The experiment this scale is to be applied to.  Needed because some
        scales have parameters estimated from data.
        
    channel : Str
        Which channel to scale.  Needed because some scales have parameters
        estimated from data.
        
    condition : Str
        What condition to scale.  Needed because some scales have parameters
        estimated from the a condition.  Must be a numeric condition; else
        instantiating the scale should fail.
        
    statistic : Tuple(Str, Str)
        What statistic to scale.  Needed because some scales have parameters
        estimated from a statistic.  The statistic must be numeric or an
        iterable of numerics; else instantiating the scale should fail.
        
    mpl_params : Dict
        A dictionary of named parameters to pass to plt.xscale() and 
        plt.yscale().  Sometimes estimated from data.
    """

    id = Str           
    name = Str
    
    experiment = Instance("cytoflow.experiment.Experiment")
    
    # what are we using to parameterize the scale?  set one of these; if
    # multiple are set, the first is used.
    channel = Str
    condition = Str
    statistic = Tuple(Str, Str)

    mpl_params = Dict()

    def __call__(self, data):
        """
        Transforms `data` using this scale.  Must know how to handle int, float,
        and lists, tuples, numpy.ndarrays and pandas.Series of int or float.
        Must return the same type passed.
        
        Careful!  May return `NaN` if the scale domain doesn't match the data 
        (ie, applying a log10 scale to negative numbers.
        """
        
    def inverse(self, data):
        """
        Transforms 'data' using the inverse of this scale.  Must know how to 
        handle int, float, and list, tuple, numpy.ndarray and pandas.Series of
        int or float.  Returns the same type as passed.
        """
        
    def clip(self, data):
        """
        Clips the data to the scale's domain.
        """
        
    def color_norm(self):
        """
        Return an instance of matplotlib.colors.Normalize, which is used to
        correctly scale a color bar.
        """
        
        
class ScaleMixin(HasStrictTraits):
    def __init__(self, **kwargs):
        
        # run the traits constructor
        HasStrictTraits.__init__(self, **kwargs)
        
        # check that the channel, condition, or statistic is either numeric or
        # an iterable of numerics
        if self.condition:
            if not is_numeric(self.experiment[self.condition]):
                raise CytoflowError("Tried to scale the non-numeric condition {}"
                                    .format(self.condition))
                
        elif self.statistic[0]:
            stat = self.experiment.statistics[self.statistic]
            if is_numeric(stat):
                return
            else:
                try:
                    for x in stat:
                        for y in x:
                            if not isinstance(y, numbers.Number):
                                raise CytoflowError("Tried to scale a non-numeric "
                                                    "statistic {}"
                                                    .format(self.statistic))
                except TypeError:
                    raise CytoflowError("Tried to scale a non-numeric "
                                        "statistic {}"
                                        .format(self.statistic))
    
# maps name -> scale object
_scale_mapping = {}
_scale_default = "linear"

def scale_factory(scale, experiment, **scale_params):
    scale = scale.lower()
        
    if scale not in _scale_mapping:
        raise CytoflowError("Unknown scale type {0}".format(scale))
        
    return _scale_mapping[scale](experiment = experiment, **scale_params)
 
def register_scale(scale_class):
    _scale_mapping[scale_class.name] = scale_class
    
def set_default_scale(scale):
    global _scale_default
    
    scale = scale.lower()
    if scale not in _scale_mapping:
        raise CytoflowError("Unknown scale type {0}".format(scale))
    
    _scale_default = scale

# register the new scales
import cytoflow.utility.linear_scale   # @UnusedImport
import cytoflow.utility.log_scale      # @UnusedImport
import cytoflow.utility.logicle_scale  # @UnusedImport

# this scale is REALLY SLOW.  If you want it for your analysis, you can
# import it into your script, that will register it with the global list.

# import cytoflow.utility.hlog_scale     # @UnusedImport


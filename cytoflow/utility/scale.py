#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
cytoflow.utility.scale
----------------------
'''

import numbers

from traits.api import Interface, Str, Dict, Instance, Tuple, Array

from .cytoflow_errors import CytoflowError
from .util_functions import is_numeric
from traits.has_traits import HasStrictTraits

class IScale(Interface):
    """
    An interface for various ways we could rescale flow data.
    
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
        
    data : array_like
        What raw data to scale.
    """

    id = Str           
    name = Str
    
    experiment = Instance("cytoflow.experiment.Experiment")
    
    # what are we using to parameterize the scale?  set one of these; if
    # multiple are set, the first is used.
    channel = Str
    condition = Str
    statistic = Tuple(Str, Str)
    error_statistic = Tuple(Str, Str)
    data = Array
    
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
        
    def norm(self, vmin = None, vmax = None):
        """
        Return an instance of matplotlib.colors.Normalize, which normalizes
        this scale to [0, 1].  Among other things, this is used to correctly
        scale a color bar.
        """
        
        
class ScaleMixin(HasStrictTraits):
    def __init__(self, **kwargs):
        
        # run the traits constructor
        super().__init__(**kwargs)
        
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
                except TypeError as e:
                    raise CytoflowError("Error scaling statistic {}"
                                        .format(self.statistic)) from e
    
# maps name -> scale object
_scale_mapping = {}
_scale_default = "linear"

def scale_factory(scale, experiment, **scale_params):
    """
    Make a new instance of a named scale.
    
    Parameters
    ----------
    scale : string
        The name of the scale to build
        
    experiment : Experiment
        The experiment to use to parameterize the new scale.
        
    **scale_params : kwargs
        Other parameters to pass to the scale constructor
    """
    
    scale = scale.lower()
        
    if scale not in _scale_mapping:
        raise CytoflowError("Unknown scale type {0}".format(scale))
        
    return _scale_mapping[scale](experiment = experiment, **scale_params)
 
def register_scale(scale_class):
    """
    Register a new scale for the :func:`scale_factory` and :class:`.ScaleEnum`.
    """
    
    _scale_mapping[scale_class.name] = scale_class
    
def set_default_scale(scale):
    """
    Set a default scale for :class:`.ScaleEnum`
    """
    
    global _scale_default
    
    scale = scale.lower()
    if scale not in _scale_mapping:
        raise CytoflowError("Unknown scale type {0}".format(scale))
    
    _scale_default = scale
    
def get_default_scale():
    return _scale_default

# register the new scales
import cytoflow.utility.linear_scale   # @UnusedImport
import cytoflow.utility.log_scale      # @UnusedImport
import cytoflow.utility.logicle_scale  # @UnusedImport

# this scale is REALLY SLOW.  If you want it for your analysis, you can
# import it into your script, that will register it with the global list.

# import cytoflow.utility.hlog_scale     # @UnusedImport


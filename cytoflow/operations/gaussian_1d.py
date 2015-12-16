'''
Created on Dec 16, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Python, \
                       Instance, Tuple, Bool, Constant, provides
import numpy as np
import fcsparser
import warnings
import matplotlib.pyplot as plt
import math
import sklearn.mixture

from cytoflow.operations import IOperation
from cytoflow.views import IView
from cytoflow.utility import CytoflowOpError, CytoflowViewError

@provides(IOperation)

class GaussianMixture1DOp(HasStrictTraits):
    """
    This module fits a Gaussian mixture model with a specified number of
    components to a channel.
    
    Creates a new categorical metadata variable named `name`, with possible
    values `name_1` .... `name_n` where `n` is the number of components.
    An event is assigned to `name_i` category if it falls within `sigma`
    standard deviations of the component's mean.  If that is true for multiple
    categories (or if `sigma == 0.0`), the event is assigned to the category 
    with the highest posterior probability.  If the event doesn't fall into
    any category, it is assigned to `name_None`.
    
    Optionally, if `posteriors` is `True`, this module will also compute the 
    posterior probability of each event in each component.  Each component
    will have a metadata column named `name_i_Posterior` containing the
    posterior probability that that event is in that component.
    
    Finally, the same mixture model (mean and standard deviation) may not
    be appropriate for every subset of the data.  If this is the case, you
    can use the `by` attribute to specify metadata by which to aggregate
    the data before estimating (and applying) a mixture.  The number of 
    components is the same across each subset, though.
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    channel : Str
        Which channel to apply the mixture model to.
        
    num_components : Int
        How many components to fit to the data? 

    sigma : Float (default = 0.0)
        How many standard deviations on either side of the mean to include
        in each category?  If an event is in multiple components, assign it
        to the component with the highest posterior probability.  If 
        `sigma == 0.0`, categorize *all* the data by assigning each event to
        the component with the highest posterior probability.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will fit the model 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    scale : Enum("linear", "log") (default = "linear")
        Re-scale the data before fitting the data?
        
        
     
    """
    
    
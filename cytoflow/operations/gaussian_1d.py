'''
Created on Dec 16, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Python, \
                       Instance, Tuple, Bool, Constant, Int, Float, List, \
                       Enum, provides, DelegatesTo
import numpy as np
import fcsparser
import warnings
import matplotlib.pyplot as plt
import math
from sklearn import mixture
import pandas as pd

from cytoflow import Experiment, HistogramView

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
        
    num_components : Int (default = 2)
        How many components to fit to the data?  Must be >= 2.

    sigma : Float (default = 0.0)
        How many standard deviations on either side of the mean to include
        in each category?  If an event is in multiple components, assign it
        to the component with the highest posterior probability.  If 
        `sigma == 0.0`, categorize *all* the data by assigning each event to
        the component with the highest posterior probability.  Must be >= 0.0.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will fit the model 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    scale : Enum("linear", "log") (default = "linear")
        Re-scale the data before fitting the data?  
        TODO - not currently implemented.
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.gaussian_1d')
    friendly_id = Constant("1D Gaussian Mixture")
    
    name = CStr()
    channel = Str()
    num_components = Int(2)
    sigma = Float(0.0)
    by = List(Str)
    
    # scale = Enum("linear", "log")
    
    _gmms = Dict(Tuple, Instance(mixture.GMM))
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the Gaussian mixture model parameters
        """
        
        if not experiment:
            raise CytoflowOpError("No experiment specified")

        if self.channel not in experiment.data:
            raise CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.channel))
            
        if self.num_components < 2:
            raise CytoflowOpError("num_components must be >= 2") 
       
        for b in self.by:
            if b not in experiment.data:
                raise CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))
            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
                
        if self.by:
            for group, data_subset in experiment.data.groupby(self.by):
                x = data_subset[self.channel].reset_index(drop = True)
                gmm = mixture.GMM(n_components = self.num_components)
                gmm.fit(x[:, np.newaxis], random_state = 1)
                
                if not gmm._converged:
                    raise CytoflowOpError("Estimator didn't converge"
                                          " for group {0}"
                                          .format(group))
                
                self._gmms[group] = gmm 
        else:
            x = experiment.data[self.channel].reset_index(drop = True)
            gmm = mixture.GMM(n_components = self.num_components)
            gmm.fit(x[:, np.newaxis])
            
            if not gmm._converged:
                raise CytoflowOpError("Estimator didn't converge")
            
            self._gmms[()] = gmm
                
    
    def apply(self, experiment):
        """
        Assigns new metadata to events using the mixture model estimated
        in `estimate`.
        """
            
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        # make sure name got set!
        if not self.name:
            raise CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")

        if self.name in experiment.data.columns:
            raise CytoflowOpError("Experiment already has a column named {0}"
                                  .format(self.name))
        
        if not self._gmms:
            raise CytoflowOpError("No components found.  Did you forget to "
                                  "call estimate()?")

        if self.channel not in experiment.data:
            raise CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.channel))
            
        if self.num_components < 2:
            raise CytoflowOpError("num_components must be >= 2") 
       
        for b in self.by:
            if b not in experiment.data:
                raise CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))
            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
                
            for groups, _ in self._gmms:
                for group in groups:
                    if not group in self.by:
                        raise CytoflowOpError("Mismatch between groups in "
                                              "self.by and previously estimated "
                                              "models.  Did you forget to "
                                              "call estimate()?")
                           
        if self.sigma < 0.0:
            raise CytoflowOpError("sigma must be >= 0.0")
        
        new_experiment = experiment.clone()
        
        # what we DON'T want to do is iterate through event-by-event.
        # the more of this we can push into numpy, sklearn and pandas,
        # the faster it's going to be.
        
        if self.by:
            groupby = new_experiment.data.groupby(self.by)
            
        for group, gmm in self._gmms:
            if group == (): # no groups, only one mixture model
                data = new_experiment.data
            else:
                data = groupby.get_group(groups)

            x = data[self.channel][:, np.newaxis]
            
            posteriors = gmm.predict_proba(x)
            
            if self.sigma > 0.0:
                for c in self.num_components:
                    lo = (gmm.means_[c][0] 
                          - self.sigma * np.sqrt(gmm.covars_[c][0]))
                    hi = (gmm.means_[c][0] 
                          + self.sigma * np.sqrt(gmm.covars_[c][0]))       
    
    def default_view(self):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
        
        Returns
        -------
            IView : an IView, call plot() to see the diagnostic plot.
        """
        return GaussianMixture1DView(op = self)
    
@provides(IView)
class GaussianMixture1DView(HistogramView):
    """
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
        
    op : Instance(GaussianMixture1DOp)
        The op whose parameters we're viewing.
    """
    
    id = 'edu.mit.synbio.cytoflow.view.gaussianmixture1dview'
    friendly_id = "1D Gaussian Mixture Diagnostic Plot"
    
    # TODO - why can't I use GaussianMixture1DOp here?
    op = Instance(IOperation)
    name = DelegatesTo('op')
    channel = DelegatesTo('op')
    huefacet = DelegatesTo('op', 'name')
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        """
        
        if not self.huefacet:
            raise CytoflowViewError("didn't set GaussianMixture1DOp.name")
        
        try:
            temp_experiment = self.op.apply(experiment)
            super(GaussianMixture1DView, self).plot(temp_experiment, **kwargs)
        except CytoflowOpError as e:
            raise CytoflowViewError(e.__str__())
        
        
    
'''
Created on Dec 16, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, Dict, Any, \
                       Instance, Bool, Constant, Int, Float, List, \
                       provides, DelegatesTo
import numpy as np
import matplotlib.pyplot as plt
from sklearn import mixture
from scipy import stats
import pandas as pd
import seaborn as sns

from cytoflow.views.histogram import HistogramView

from cytoflow.operations import IOperation
from cytoflow.views import IView
from cytoflow.utility import CytoflowOpError, CytoflowViewError, num_hist_bins

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
        
    posteriors : Bool (default = False)
        If `True`, add one column per component giving the posterior probability
        that each event is in each component.  Useful for filtering out
        low-probability events.
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.gaussian_1d')
    friendly_id = Constant("1D Gaussian Mixture")
    
    name = CStr()
    channel = Str()
    num_components = Int(2)
    sigma = Float(0.0)
    by = List(Str)
    
    # scale = Enum("linear", "log")
    
    posteriors = Bool(False)
    
    # the key is either a single value or a tuple
    _gmms = Dict(Any, Instance(mixture.GMM))
    
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
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda x: True)
            
        for group, data_subset in groupby:
            x = data_subset[self.channel].reset_index(drop = True)
            gmm = mixture.GMM(n_components = self.num_components,
                              random_state = 1)
            gmm.fit(x[:, np.newaxis])
            
            if not gmm.converged_:
                raise CytoflowOpError("Estimator didn't converge"
                                      " for group {0}"
                                      .format(group))
           
            self._gmms[group] = gmm
    
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
            
        if (self.name + "_Posterior") in experiment.data:
            raise CytoflowOpError("Column {0} already found in the experiment"
                                  .format(self.name + "_Posterior"))

        if self.num_components < 2:
            raise CytoflowOpError("num_components must be >= 2") 

        if self.posteriors:
            for i in range(0, self.num_components):
                col_name = "{0}_{1}_Posterior".format(self.name, i+1)
                if col_name in experiment.data:
                    raise CytoflowOpError("Column {0} already found in the experiment"
                                  .format(col_name))
       
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
                           
        if self.sigma < 0.0:
            raise CytoflowOpError("sigma must be >= 0.0")
        
        new_experiment = experiment.clone()
        name_dtype = np.dtype("S{0}".format(len(self.name) + 5))
        new_experiment.data[self.name] = \
            np.full(len(new_experiment.data.index), "", name_dtype)
        new_experiment.metadata[self.name] = {'type' : 'meta'}
        new_experiment.conditions[self.name] = "category"
        
        if self.posteriors:
            for i in range(0, self.num_components):
                col_name = "{0}_{1}_Posterior".format(self.name, i+1)
                new_experiment.data[col_name] = \
                    np.full(len(new_experiment.data.index), 0.0)
                new_experiment.metadata[col_name] = {'type' : 'meta'}
                new_experiment.conditions[col_name] = "float"
        
        # what we DON'T want to do is iterate through event-by-event.
        # the more of this we can push into numpy, sklearn and pandas,
        # the faster it's going to be.
        
        if self.by:
            groupby = new_experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that
            # contains all the events
            groupby = new_experiment.data.groupby(lambda x: True)
        
        for group, data_subset in groupby:
            gmm = self._gmms[group]
            x = data_subset[self.channel]
            
            # make a preliminary assignment
            predicted = gmm.predict(x[:,np.newaxis])
            
            # if we're doing sigma-based gating, for each component check
            # to see if the event is in the sigma gate.
            if self.sigma > 0.0:
                
                # make a quick dataframe with the value and the predicted
                # component
                gate_df = pd.DataFrame({"x" : x, "p" : predicted})

                # for each component, get the low and the high threshold
                for c in range(0, self.num_components):
                    lo = (gmm.means_[c][0]    # @UnusedVariable
                          - self.sigma * np.sqrt(gmm.covars_[c][0]))
                    hi = (gmm.means_[c][0]    # @UnusedVariable
                          + self.sigma * np.sqrt(gmm.covars_[c][0]))
                    
                    # and build an expression with numexpr so it evaluates fast!
                    gate_bool = gate_df.eval("p == @c and x >= @lo and x <= @hi").values
                    predicted[np.logical_and(predicted == c, gate_bool == False)] = -1
        
            # TODO - sort component assignments by mean.  eg, the lowest
            # mean should be component 1, then component 2, etc.
        
            cname = np.full(len(predicted), self.name + "_", name_dtype)
            predicted_str = np.char.mod('%d', predicted + 1) 
            predicted_str = np.char.add(cname, predicted_str)
            predicted_str[predicted == -1] = "{0}_None".format(self.name)

            # it took me a few goes to get this slicing right.  the key
            # is the use of .loc so you're not chaining lookups
            new_experiment.data.loc[groupby.groups[group], self.name] = \
                predicted_str
                    
            if self.posteriors:
                probability = gmm.predict_proba(x[:,np.newaxis])
                #print probability[:, 0]
                for i in range(0, self.num_components):
                    col_name = "{0}_{1}_Posterior".format(self.name, i+1)
                    #print probability[i]
                    new_experiment.data.loc[groupby.groups[group], col_name] = \
                        probability[:, i]
                    
        return new_experiment
    
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
        
    group : Python (default: None)
        The subset of data to display.  Must match one of the keys of 
        `op._gmms`.  If `None` (the default), display a plot for each subset.
    """
    
    id = 'edu.mit.synbio.cytoflow.view.gaussianmixture1dview'
    friendly_id = "1D Gaussian Mixture Diagnostic Plot"
    
    # TODO - why can't I use GaussianMixture1DOp here?
    op = Instance(IOperation)
    name = DelegatesTo('op')
    channel = DelegatesTo('op')
    huefacet = DelegatesTo('op', 'name')
    group = Any(None)
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        """
        
        if not self.huefacet:
            raise CytoflowViewError("didn't set GaussianMixture1DOp.name")
        
        if not self.op._gmms:
            raise CytoflowViewError("Didn't find a model. Did you call "
                                    "estimate()?")
            
        if self.group and self.group not in self.op._gmms:
            raise CytoflowViewError("didn't find group {0} in op._gmms"
                                    .format(self.group))
        
        # if `group` wasn't specified, make a new plot per group.
        if self.op.by and not self.group:
            groupby = experiment.data.groupby(self.op.by)
            for group, _ in groupby:
                GaussianMixture1DView(op = self.op,
                                      group = group).plot(experiment, **kwargs)
                plt.title("{0} = {1}".format(self.op.by, group))
            return
                
        temp_experiment = experiment.clone()
        if self.group:
            groupby = experiment.data.groupby(self.op.by)
            temp_experiment.data = groupby.get_group(self.group)
        
        try:
            temp_experiment = self.op.apply(temp_experiment)
        except CytoflowOpError as e:
            raise CytoflowViewError(e.__str__())

        # plot the group's histogram, colored by component
        super(GaussianMixture1DView, self).plot(temp_experiment, **kwargs)
        
        # plot the actual distribution on top of it.
        # we want to scale the plots so they have the same area under the
        # curve as the histograms.  we'll do so with the predicted group
        # assignments (as opposed to the values of self.name) because we
        # want the scale to be the same regardless of self.op.sigma
    
        gmm = self.op._gmms[self.group] if self.group else self.op._gmms[True]
        
        predicted = gmm.predict(temp_experiment[self.channel][:, np.newaxis])
        temp_experiment.data[self.name + "_predicted"] = predicted
                
        for i in range(0, len(gmm.means_)):
            groupby = temp_experiment.data.groupby(self.name + "_predicted")
            group_data = groupby.get_group(i).reset_index(drop = True)
            xmin = np.amin(group_data[self.channel])
            xmax = np.amax(group_data[self.channel])
            hist_bin_width = (xmax - xmin) / num_hist_bins(group_data[self.channel])
            pdf_scale = hist_bin_width * len(group_data.index)
            
            # okay, so maybe we'll fudge a little.
            pdf_scale *= 1.2
            
            plt_min, plt_max = plt.gca().get_xlim()
            x = np.linspace(plt_min, plt_max, 100)
            mean = gmm.means_[i][0]
            stdev = np.sqrt(gmm.covars_[i][0])
            y = stats.norm.pdf(x, mean, stdev) * pdf_scale
            color_i = i % len(sns.color_palette())
            color = sns.color_palette()[color_i]
            plt.plot(x, y, color = color)
            
#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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

"""
cytoflow.operations.registration
------------------------------------

The `registration` module contains two classes:

`RegistrationOp` -- warps channels to bring areas of high density into registration

`RegistrationDiagnostic` -- a diagnostic view to make sure
that `RegistrationOp` performed correctlyu
"""

from traits.api import (HasStrictTraits, Str, Dict, Int, List, 
                        Float, Constant, provides, Instance, Union,
                        Callable, Any, Enum, Tuple)
import numpy as np
import pandas as pd
import scipy.signal
import sklearn
from sklearn.neighbors import KernelDensity
from statsmodels.nonparametric.bandwidths import bw_scott, bw_silverman
from skfda import FDataGrid
from skfda.preprocessing.registration import landmark_elastic_registration_warping, invert_warping
        
import matplotlib.pyplot as plt

import cytoflow.utility as util
from cytoflow.views import IView
from cytoflow.views.kde_1d import _kde_support

from .i_operation import IOperation

@provides(IOperation)
class RegistrationOp(HasStrictTraits):
    """
    `RegistrationOp` is used to *register* different data sets with eachother.
    It identifies areas of high density that are shared across all most of the
    data sets, then applies a warp function to align those areas of high
    density. This is commonly used to correct sample-to-sample variation
    across large data sets. This is *not* a multidimensional algorithm --
    if you apply it to multiple channels, each channel is warped 
    independently.
    
    Attributes
    ----------
   
    channels : List(Str)
        The channels to register.
        
    scale : Dict(Str : {"linear", "logicle", "log"})
        How to scale the channels before registering.
        
    by : List(Str)
        Which conditions to use to group samples? These are usually
        experimental conditions, not gates!
        
    subset : Str
        How to filter the data before estimating the transformation?
                
    kernel : Str (default = ``gaussian``)
        The kernel to use for the kernel density estimate. Choices are:
        
            - ``gaussian`` (the default)
            - ``tophat``
            - ``epanechnikov``
            - ``exponential``
            - ``linear``
            - ``cosine``
            
    bw : Str or Float (deafult = ``scott``)
        The bandwidth for the kernel, controls how lumpy or smooth the
        kernel estimate is.  Choices are:
        
            - ``scott`` (the default) - ``1.059 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
            - ``silverman`` - ``.9 * A * nobs ** (-1/5.)``, where ``A`` is ``min(std(X),IQR/1.34)``
            
        If a float is given, it is the bandwidth.   Note, this is in 
        scaled units, not data units.
        
    gridsize : int (default = 200)
        How many locations should we evaluate the kernel?
        
    
    Notes
    -----
    The registration algorithm follows the approach from the ``warpSet`` 
    function in the R/Bioconductor ``flowStats`` package. The precise details
    differ depending on what is available in the scientific Python ecosystem,
    but the overall flow remains the same. For each channel:
    
    - Rescale the data (if requested)
    
    - Smooth the data using a kernel density estimate
    
    - Use a peak-finding algorithm to find landmarks in the distribution
    
    - Use 1-dimensional K-means across groups to group landmarks together
    
    - Determine the (scaled) mean of each group. These are the "destinations" for our 
      warp functions.
      
    - Using tools from functional data analysis, compute a "warp" function
      that can be applied to each group to move the landmarks to the median.
      
    - Apply the warp function to the underlying data, scaling and then 
      inverting as you do so.
      
    Every step except the last is performed by the `estimate` function. The 
    diagnostic plot shows the smoothed distribution, the peaks, their 
    clusters and means, and the warped (smoothed) distribution.
    
    Examples
    --------
    
    TODO
        
    """
    
    # traits
    id = Constant('cytoflow.operations.register')
    friendly_id = Constant("Density Registration")
    
    name = Constant("Registration")
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    by = List(Str)
    
    # Smoothing
    
    kernel = Enum('gaussian','tophat','epanechnikov','exponential','linear','cosine')
    bw = Union(Enum('scott', 'silverman'), Float)
    gridsize = Int(200)

    # these are really only saved to support plotting
    _scale = Dict(Str, Instance(util.IScale))
    _groups = List(Any)
    _support = Dict(Str, np.ndarray) # channel --> kde support
    _kde = Dict(Str, Dict(Any, np.ndarray)) # channel, group --> kde density
    _peaks = Dict(Str, Dict(Any, List(Float))) # channel, group --> peaks
    _clusters = Dict(Str, Dict(Any, List(Union(Int, None)))) # channel, group --> cluster assignments
    _means = Dict(Str, List(Union(Float, None))) # channel --> cluster medians
    
    _warping = Dict(Str, Callable) # channel --> warping


    def estimate(self, experiment, subset = None): 
        """
        Estimate the calibration coefficients from the beads file.
        
        Parameters
        ----------
        experiment : `Experiment`
            The experiment used to compute the calibration.
            
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")

        if len(self.channels) != len(set(self.channels)):
            raise util.CytoflowOpError('channels', 
                                       "Must not duplicate channels")

        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                      .format(c))
                
        for c in self.scale:
            if c not in self.channels:
                raise util.CytoflowOpError('channels',
                                           "Scale set for channel {0}, but it isn't "
                                           "'channels'"
                                           .format(c))
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                
        if subset:
            try:
                experiment = experiment.query(subset)
            except:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(subset))
                
            if len(experiment) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no events"
                                             .format(subset))
                
        if self.by:
            groupby = experiment.data.groupby(self.by, observed = False)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True, observed = False)
                    
        self._warping.clear()
        self._scale.clear()
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        for c in self.channels:
            if c in self.scale:
                self._scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
            else:
                self._scale[c] = util.scale_factory(util.get_default_scale(), experiment, channel = c)
   
        warpings = {}
        for channel in self.channels:
            
            # scikit-fda requires that all the functions (in this case, the
            # KDEs) be on the same support.
            
            all_data = pd.concat([group_data[channel] for _, group_data in groupby],
                                 ignore_index = True, sort = True)
            all_scaled_data = self._scale[channel](all_data)
            
            if self.bw == 'scott':
                bw = bw_scott(all_scaled_data)
            elif self.bw == 'silverman':
                bw = bw_silverman(all_scaled_data)
            else:
                bw = self.bw
                                
            # support we calculate on is scaled, not in data units.
            support = _kde_support(all_scaled_data, bw, self.gridsize, 3.0, 
                                   (-np.inf, np.inf))
                        
            # but the support we SAVE is in DATA UNITS.
            support = self._scale[channel].inverse(support)
            
            # the support must be strictly increasing, so remove duplicates
            # (ie, values that were clipped in the inverse)
            self._support[channel] = support = np.unique(support)
            
            # re-scale the (inverted) support
            support = self._scale[channel](support)
                                               
            all_peaks = []
            self._kde[channel] = {}
            self._peaks[channel] = {}
            for group, group_data in groupby:
                
                #compute the KDE 
                scaled_data = self._scale[channel](group_data[channel])
                
                kde = KernelDensity(kernel = self.kernel, bandwidth = bw)
                kde.fit(scaled_data.to_numpy()[:, np.newaxis])
                density = np.exp(kde.score_samples(support[:, np.newaxis]))
                self._kde[channel][group] = density
                
                # find the peaks
                peaks = scipy.signal.find_peaks(density)[0].tolist()
                peaks = [support[p] for p in peaks]
                self._peaks[channel][group] = [self._scale[channel].inverse(p) for p in peaks]

                if not all_peaks:
                    all_peaks = peaks
                else:
                    all_peaks.extend(peaks)
        
            # cluster the peaks ACROSS GROUPS. we want the minumum number
            # of clusters where no two peaks in the same group are
            # assigned to the same cluster.
        
            self._clusters[channel] = {}
            for n_clusters in range(1, len(all_peaks)):
                km = sklearn.cluster.KMeans(n_clusters = n_clusters,
                                            random_state = 0)
                km.fit(np.array(all_peaks).reshape(-1, 1))
        
                for group, _ in groupby:
                    peaks = self._scale[channel](self._peaks[channel][group])
                    cluster_assignments = km.predict(np.array(peaks).reshape(-1, 1)).tolist()
        
                    # check for duplicates
                    if len(cluster_assignments) != len(set(cluster_assignments)):
                        continue
        
                    self._clusters[channel][group] = cluster_assignments
    
                if len(self._clusters[channel]) == groupby.ngroups:
                    break
                                
            # get rid of clusters that don't have a peak in each group
            for cluster in range(0, n_clusters):
                in_group = [cluster in self._clusters[channel][group] for group in self._clusters[channel]]
                if not all(in_group):
                    for group in self._clusters[channel]:
                        try:
                            clust_idx = self._clusters[channel][group].index(cluster) # after previous, should only be in here once!
                            self._clusters[channel][group][clust_idx] = None  
                        except ValueError:
                            # value wasn't in the list
                            pass
        
            # now that we have clusters, compute the median of each cluster
            self._means[channel] = []
            for cluster in range(n_clusters):
                clust_peaks = []
            
                for group, _ in groupby:
                    peaks = self._scale[channel](self._peaks[channel][group])
                    cluster_assignments = self._clusters[channel][group]
                    try:
                        peak_idx = cluster_assignments.index(cluster)
                    except ValueError:
                        # this group didn't have a peak assigned to this cluster
                        continue
                    
                    clust_peaks.append(peaks[peak_idx])
                                
                if clust_peaks:
                    self._means[channel].append(self._scale[channel].inverse(np.mean(clust_peaks)))
                else:
                    self._means[channel].append(None)     
                

            # compute the warping to register the landmarks to the means
            # we compute the warping on SCALED data
            fd = FDataGrid(data_matrix = [self._scale[channel](self._kde[channel][group]) for group in self._kde[channel]], 
                           grid_points = self._scale[channel](self._support[channel]))
            
            landmarks = [[self._peaks[channel][group][i] 
                          for i in range(len(self._peaks[channel][group]))
                          if self._clusters[channel][group][i] is not None] 
                         for group in self._peaks[channel]]

            landmarks = [self._scale[channel](el) for el in ([sorted(s) for s in landmarks])]

            location = [s for s in self._means[channel] if s is not None]
            location = self._scale[channel](sorted(location))

            warping = landmark_elastic_registration_warping(fd, 
                                                            landmarks = landmarks,
                                                            location = location)
            
            # i don't know why i need to do this :(
            # clearly i don't understand FDA
            warpings[channel] = invert_warping(warping)
            
        # # set atomically to support the GUI
        self._warping = warpings
        # self._warp_functions = warp_functions
                
    
    def apply(self, experiment):
        """
        Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : `Experiment`
            the experiment to which this operation is applied
            
        Returns
        -------
        Experiment 
            A new experiment with the specified channels warped to bring their
            density maxima into registration.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")

        if not self._warping:
            raise util.CytoflowOpError(None,
                                       "Registration warp not found. "
                                       "Did you forget to call estimate()?")
        
        if not set(self.channels) <= set(experiment.channels):
            raise util.CytoflowOpError('units',
                                       "Warp channels don't match experiment channels")
        
        if set(self.channels) != set(self._warping):
            raise util.CytoflowOpError('units',
                                       "Registration warp doesn't match channels. "
                                       "Did you forget to call estimate()?")
            
        new_experiment = experiment.clone(deep = True)
        
        if self.by:
            groupby = experiment.data.groupby(self.by, observed = False)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True, observed = False)
            
        for channel in self.channels:
            scale = self._scale[channel]
            warping = self._warping[channel]
            for group_idx, (_, group_data) in enumerate(groupby):
                new_experiment.data.loc[group_data.index, channel] = \
                    scale.inverse(warping(scale(group_data[channel])))[group_idx]
                
        if 'range' in new_experiment.metadata[channel]:
            new_experiment.metadata[channel]['range'] = max(warping(new_experiment.metadata[channel]['range']))
        if 'voltage' in new_experiment.metadata[channel]:
            del new_experiment.metadata[channel]['voltage']
                
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        return new_experiment    
        
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to see if the peak finding is working.
        
        Returns
        -------
        `IView`
            An diagnostic view, call `BeadCalibrationDiagnostic.plot` to 
            see the diagnostic plots
        """

        v = RegistrationDiagnosticView(op = self)
        v.trait_set(**kwargs)
        return v
    

@provides(IView)
class RegistrationDiagnosticView(HasStrictTraits):
    """
    A diagnostic view for `RegistrationOp`.
        
    Plots the smoothed histogram of the bead data; the peak locations;
    a scatter plot of the raw bead fluorescence values vs the calibrated unit 
    values; and a line plot of the model that was computed.  Make sure that the
    relationship is linear; if it's not, it likely isn't a good calibration!
    
    Attributes
    ----------
    op : Instance(`BeadCalibrationOp`)
        The operation instance whose diagnostic we're plotting.  Set 
        automatically if you created the instance using 
        `BeadCalibrationOp.default_view`.

    """
    
    # traits   
    id = Constant("cytoflow.views.registrationdiagnosticview")
    friendly_id = Constant("Registration Diagnostic")
        
    op = Instance(RegistrationOp)
    
    def enum_plots(self, experiment):
        """
        Enumerate the named plots we can make from this set of statistics.
        
        Returns
        -------
        iterator
            An iterator across the possible plot names.
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
            
        if self.op._support:
            return util.IterByWrapper(iter(self.op._support), [])
        else:
            return util.IterByWrapper(iter([]), [])
        
           
    def plot(self, experiment, plot_name = None):
        """
        Plots the diagnostic view.
        
        Parameters
        ----------
        experiment : `Experiment`
            The experiment used to create the diagnostic plot.
        
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.op._support:
            raise util.CytoflowViewError(None, "Must estimate the operations parameters first!")
        
        if plot_name is None and len(self.op._support) == 1:
            plot_name = list(self.op._support)[0]
        
        if not plot_name:
            raise util.CytoflowViewError('plot_name', "Must set 'plot_name' to one of the channels that was estimated!")
        
        if not plot_name in self.op._support:
            raise util.CytoflowViewError('plot_name', 
                                         "Channel {} was not estimated!"
                                         .format(self.channel))
            
        channel = plot_name
        scale = self.op._scale[channel]
        groups = self.op._kde[channel].keys()
        
        kde_support = self.op._support[channel]
        
        # let's not use the FacetGrid stuff here, eh?
        fig, axes = plt.subplots(len(groups), 1, sharex = True, constrained_layout = True)
        fig.set_constrained_layout_pads(hspace = 0.0, h_pad = 0.0)
        for i, group in enumerate(groups):
            ax = axes[i]
            ax.spines['top'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylabel(', '.join([str(g) for g in group]))
            ax.set_xscale(scale.name, **scale.get_mpl_params(plt.gca().get_xaxis()))
            ax.grid(False)
            ax.tick_params(axis = 'y', which = "both", left = False, labelleft = False)
            if i < len(self.op._groups) - 1:
                ax.tick_params(axis = 'x', which = "both", bottom = False, labelbottom = False)

            # plot the density
            kde_density = self.op._kde[channel][group]

            x = kde_support
            before_artist = axes[i].plot(x, kde_density)
            
            scaled_support = scale(kde_support)
            warped_x = self.op._warping[channel](scaled_support)[i]
            warped_x = scale.inverse(warped_x)
            
            after_artist = axes[i].plot(warped_x, kde_density, color = 'r')
            
            if i == 0:
                before_artist[0].set_label("Before registration")
                after_artist[0].set_label("After registration")
            
            # plot the peaks
            peaks = self.op._peaks[channel][group]
            for peak in peaks:
                ax.axvline(peak, color = 'b', linestyle = '--')
            
            # plot cluster peaks, means
            means = self.op._means[channel]
            cluster_assignments = self.op._clusters[channel][group]
            for cluster_idx, mean in enumerate(means):
                if mean is None:
                    continue
            
                ax.axvline(mean, color = 'grey', linestyle = '-')
            
                try:
                    peak_idx = cluster_assignments.index(cluster_idx)
                    y = 0.1
                    if abs(scale(peaks[peak_idx]) - scale(mean)) > 0.01:
                        ax.annotate("", xytext = (peaks[peak_idx], y), xy = (mean, y), 
                                    arrowprops=dict(width = 1, headwidth = 5, headlength = 3, color = 'k'))
                except ValueError:
                    # this group didn't have a peak assigned to this cluster
                    continue
            
            # axes[i].set_title("{} = {}".format(', '.join(self.op.by), 
            #                                    ', '.join([str(g) for g in group])))
        
        fig.draw_without_rendering()
        plt.xlabel(channel)
        fig.supylabel(', '.join(self.op.by))
        # plot a figure legend
        fig.legend(loc = 'outside right upper')   
        
        # clean up layout issues
        # fig.tight_layout()         
        
            

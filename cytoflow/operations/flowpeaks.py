#!/usr/bin/env python3.8
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
cytoflow.operations.flowpeaks
-----------------------------
'''

import matplotlib.pyplot as plt
from warnings import warn

from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, 
                        Constant, List, provides, Array, Function)

import numpy as np
import sklearn.cluster
import scipy.stats
import scipy.optimize
import scipy.ndimage

import pandas as pd

import copy

from cytoflow.views import IView, HistogramView, ScatterplotView
import cytoflow.utility as util

from .i_operation import IOperation
from .base_op_views import By1DView, By2DView, AnnotatingView, NullView

@provides(IOperation)
class FlowPeaksOp(HasStrictTraits):
    """
    This module uses the **flowPeaks** algorithm to assign events to clusters in
    an unsupervised manner.
    
    Call :meth:`estimate` to compute the clusters.
      
    Calling :meth:`apply` creates a new categorical metadata variable 
    named ``name``, with possible values ``{name}_1`` .... ``name_n`` where 
    ``n`` is the number of clusters estimated.
    
    The same model may not be appropriate for different subsets of the data set.
    If this is the case, you can use the :attr:`by` attribute to specify 
    metadata by which to aggregate the data before estimating (and applying) 
    a model.  The number of clusters is a model parameter and it may vary in 
    each subset. 

    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    channels : List(Str)
        The channels to apply the clustering algorithm to.

    scale : Dict(Str : Enum("linear", "logicle", "log"))
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in :attr:`channels` but not in :attr:`scale`, the current 
        package-wide default (set with :func:`set_default_scale`) is used.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting ``by = ["Time", "Dox"]`` will fit the model 
        separately to each subset of the data with a unique combination of
        ``Time`` and ``Dox``.
        
    h : Float (default = 1.5)
        A scalar value by which to scale the covariance matrices of the 
        underlying density function.  (See ``Notes``, below, for more details.)
        
    h0 : Float (default = 1.0)
        A scalar value by which to smooth the covariance matrices of the
        underlying density function.  (See ``Notes``, below, for more details.)
        
    tol : Float (default = 0.5)
        How readily should clusters be merged?  Must be between 0 and 1.
        See ``Notes``, below, for more details.
        
    merge_dist : Float (default = 5)
        How far apart can clusters be before they are merged?  This is
        a unit-free scalar, and is approximately the maximum number of
        k-means clusters between peaks. 
        
    find_outliers : Bool (default = False)
        Should the algorithm use an extra step to identify outliers?
        
        .. note::
            I have disabled this code until I can try to make it faster.
        
    Notes
    -----
    
    This algorithm uses kmeans to find a large number of clusters, then 
    hierarchically merges those clusters.  Thus, the user does not need to
    specify the number of clusters in advance, and it can find non-convex
    clusters.  It also operates in an arbitrary number of dimensions.
    
    The merging happens in two steps.  First, the cluster centroids are used
    to estimate an underlying density function.  Then, the local maxima of
    the density function are found using a numerical optimization starting from
    each centroid, and k-means clusters that converge to the same local maximum
    are merged.  Finally, these clusters-of-clusters are merged if their local 
    maxima are (a) close enough, and (b) the density function between them is 
    smooth enough.  Thus, the final assignment of each event depends on the 
    k-means cluster it ends up in, and which cluster-of-clusters that k-means 
    centroid is assigned to.
    
    There are a lot of parameters that affect this process.  The k-means
    clustering is pretty robust (though somewhat sensitive to the number of 
    clusters, which is currently not exposed in the API.) The most important
    are exposed as attributes of the :class:`FlowPeaksOp` class.  These include:
    
     - :attr:`h`, :attr:`h0`: sometimes the density function is too "rough" to 
         find good local maxima.  These parameters smooth it out by widening the
         covariance matrices.  Increasing :attr:`h` makes the density rougher; 
         increasing :attr:`h0` makes it smoother.
              
    - :attr:`tol`: How smooth does the density function have to be between two 
        density maxima to merge them?  Must be between 0 and 1.
           
    - :attr:`merge_dist`: How close must two maxima be to merge them?  This 
        value is a unit-free scalar, and is approximately the number of
        k-means clusters between the two maxima.
        
    For details and a theoretical justification, see [1]_
    
    References
    ----------
    
    .. [1] Ge, Yongchao and Sealfon, Stuart C.  "flowPeaks: a fast unsupervised
       clustering for flow cytometry data via K-means and density peak finding" 
       Bioinformatics (2012) 28 (15): 2052-2058.         
  
    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        Make a little data set.
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
    
    Create and parameterize the operation.
    
    .. plot::
        :context: close-figs
        
        >>> fp_op = flow.FlowPeaksOp(name = 'Flow',
        ...                          channels = ['V2-A', 'Y2-A'],
        ...                          scale = {'V2-A' : 'log',
        ...                                   'Y2-A' : 'log'},
        ...                          h0 = 3)
        
    Estimate the clusters
    
    .. plot::
        :context: close-figs
        
        >>> fp_op.estimate(ex)
        
    Plot a diagnostic view of the underlying density
    
    .. plot::
        :context: close-figs
        
        >>> fp_op.default_view(density = True).plot(ex)

    Apply the gate
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = fp_op.apply(ex)

    Plot a diagnostic view with the event assignments
    
    .. plot::
        :context: close-figs
        
        >>> fp_op.default_view().plot(ex2)
        

    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.flowpeaks')
    friendly_id = Constant("FlowPeaks Clustering")
    
    name = Str
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    by = List(Str)
#     find_outliers = Bool(False)
    
    # parameters that control estimation, with sensible defaults
    h = util.PositiveFloat(1.5, allow_zero = False)
    h0 = util.PositiveFloat(1, allow_zero = False)
    tol = util.PositiveFloat(0.5, allow_zero = False)
    merge_dist = util.PositiveFloat(5, allow_zero = False)
    
    # estimate internals
    _kmeans = Dict(Any, Instance(sklearn.cluster.MiniBatchKMeans), transient = True)
    _means = Dict(Any, List, transient = True)
    _normals = Dict(Any, List(Function), transient = True)
    _density = Dict(Any, Function, transient = True)
    _peaks = Dict(Any, List(Array), transient = True)  
    _peak_clusters = Dict(Any, List(Array), transient = True)
    _cluster_peak = Dict(Any, List, transient = True)  # kmeans cluster idx --> peak idx
    _cluster_group = Dict(Any, List, transient = True) # kmeans cluster idx --> group idx
    _scale = Dict(Str, Instance(util.IScale), transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the k-means clusters, then hierarchically merge them.
        
        Parameters
        ----------
        experiment : Experiment
            The :class:`.Experiment` to use to estimate the k-means clusters
            
        subset : str (default = None)
            A Python expression that specifies a subset of the data in 
            ``experiment`` to use to parameterize the operation.
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
                raise util.CytoflowOpError('scale',
                                           "Scale set for channel {0}, but it isn't "
                                           "in the experiment"
                                           .format(c))
       
        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                
        if subset:
            try:
                experiment = experiment.query(subset)
            except:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' isn't valid"
                                           .format(subset))
                
            if len(experiment) == 0:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' returned no events"
                                           .format(subset))
                
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True)
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        for c in self.channels:
            if c in self.scale:
                self._scale[c] = util.scale_factory(self.scale[c], experiment, channel = c)
#                 if self.scale[c] == 'log':
#                     self._scale[c].mode = 'mask'
            else:
                self._scale[c] = util.scale_factory(util.get_default_scale(), experiment, channel = c)
                                    
        for data_group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError('by',
                                           "Group {} had no data".format(data_group))
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])
            
            # drop data that isn't in the scale range
            for c in self.channels:
                x = x[~(np.isnan(x[c]))]
            x = x.values
            
            #### choose the number of clusters and fit the kmeans
            num_clusters = [util.num_hist_bins(x[:, c]) for c in range(len(self.channels))]
            num_clusters = np.ceil(np.median(num_clusters))
            num_clusters = int(num_clusters)
            
            self._kmeans[data_group] = kmeans = \
                sklearn.cluster.MiniBatchKMeans(n_clusters = num_clusters,
                                                random_state = 0)
            
            kmeans.fit(x)
            x_labels = kmeans.predict(x)
            d = len(self.channels)

            #### use the kmeans centroids to parameterize a finite gaussian
            #### mixture model which estimates the density function
                        
            s0 = np.zeros([d, d])
            for j in range(d):
                r = x[d].max() - x[d].min()
                s0[j, j] = (r / (num_clusters ** (1. / d))) ** 0.5 
            
            means = []
            weights = []
            normals = []
                        
            for k in range(num_clusters):
                xk = x[x_labels == k]
                num_k = np.sum(x_labels == k)
                weight_k = num_k / len(x_labels)
                mu = xk.mean(axis = 0)
                means.append(mu)
                s = np.cov(xk, rowvar = False)
                
                el = num_k / (num_clusters + num_k)
                s_smooth = el * self.h * s + (1.0 - el) * self.h0 * s0
                
                n = scipy.stats.multivariate_normal(mean = mu, cov = s_smooth)
                weights.append(weight_k)
                normals.append(lambda x, n = n: n.pdf(x))
                       
            self._means[data_group] = means
            self._normals[data_group] = normals         
            self._density[data_group] = density = lambda x, weights = weights, normals = normals: np.sum([w * n(x) for w, n in zip(weights, normals)], axis = 0)
            
        ### use optimization on the finite gmm to find the local peak for 
        ### each kmeans cluster
        for data_group, data_subset in groupby:
            kmeans = self._kmeans[data_group]
            num_clusters = kmeans.n_clusters
            means = self._means[data_group]
            density = self._density[data_group]
            peaks = []
            peak_clusters = []  # peak idx --> list of clusters
                        
            min_mu = [np.inf] * len(self.channels)
            max_mu = [-1.0 * np.inf] * len(self.channels)
             
            for k in range(num_clusters):
                mu = means[k]
                for ci in range(len(self.channels)):
                    if mu[ci] < min_mu[ci]:
                        min_mu[ci] = mu[ci]
                    if mu[ci] > max_mu[ci]:
                        max_mu[ci] = mu[ci]
          
            for k in range(num_clusters):
                mu = means[k]
                f = lambda x: -1.0 * density(x)
                
                res = scipy.optimize.minimize(f, mu, method = "CG",
                                              options = {'gtol' : 1e-3})

                if not res.success:
                    warn("Peak finding failed for cluster {}: {}"
                         .format(k, res.message),
                         util.CytoflowWarning)

#                 ### The peak-searching algorithm from the paper.  works fine,
#                 ### but slow!  we get similar results with the conjugate gradient
#                 ### optimization method from scipy

#                 x0 = x = means[k]
#                 k0 = k
#                 b = beta_max[k] / 10.0
#                 Nsuc = 0
#                 n = 0
#                 
#                 while(n < 1000):
# #                     df = scipy.misc.derivative(density, x, 1e-6)
#                     df = statsmodels.tools.numdiff.approx_fprime(x, density)
#                     if np.linalg.norm(df) < 1e-3:
#                         break
#                     
#                     y = x + b * df / np.linalg.norm(df)
#                     if density(y) <= density(x):
#                         Nsuc = 0
#                         b = b / 2.0
#                         continue
#                     
#                     Nsuc += 1
#                     if Nsuc >= 2:
#                         b = min(2*b, beta_max[k])
# 
#                     ky = kmeans.predict(y[np.newaxis, :])[0]
#                     if ky == k:
#                         x = y
#                     else:
#                         k = ky
#                         b = beta_max[k] / 10.0
#                         mu = means[k]
#                         if density(mu) > density(y):
#                             x = mu
#                         else:
#                             x = y
#                             
#                     n += 1 
                                        
                merged = False
                for pi, p in enumerate(peaks):
                    # TODO - this probably only works for scaled measurements
                    if np.linalg.norm(p - res.x) < (1e-2):  
                        peak_clusters[pi].append(k)
                        merged = True
                        break
                        
                if not merged:
                    peak_clusters.append([k])
                    peaks.append(res.x)                    
            
            self._peaks[data_group] = peaks
            self._peak_clusters[data_group] = peak_clusters

        ### merge peaks that are sufficiently close
            
        cluster_peak = {}
        for data_group, data_subset in groupby:
            kmeans = self._kmeans[data_group]
            num_clusters = kmeans.n_clusters
            means = self._means[data_group]
            density = self._density[data_group]
            peaks = self._peaks[data_group]
            peak_clusters = self._peak_clusters[data_group]

            groups = [[x] for x in range(len(peaks))]
            peak_groups = [x for x in range(len(peaks))]  # peak idx --> group idx
            
                            
            def max_tol(x, y):
                f = lambda a: density(a[np.newaxis, :])
#                 lx = kmeans.predict(x[np.newaxis, :])[0]
#                 ly = kmeans.predict(y[np.newaxis, :])[0]
                n = len(x)
                n_scale = 1
#                 n_scale = np.sqrt(((nx + ny) / 2.0) / (n / num_clusters))
                
                def tol(t):
                    zt = x + t * (y - x)
                    fhat_zt = f(x) + t * (f(y) - f(x))
                    return -1.0 * abs((f(zt) - fhat_zt) / fhat_zt) * n_scale
                
                res = scipy.optimize.minimize_scalar(tol, 
                                                     bounds = [0, 1], 
                                                     method = 'Bounded')
                
                if res.status != 0:
                    raise util.CytoflowOpError(None,
                                               "tol optimization failed for {}, {}"
                                               .format(x, y))
                return -1.0 * res.fun
                
            
            def nearest_neighbor_dist(k):
                min_dist = np.inf
                
                for i in range(num_clusters):
                    if i == k:
                        continue
                    dist = np.linalg.norm(means[k] - means[i])
                    if dist < min_dist:
                        min_dist = dist
                        
                return min_dist
            
            sk = [nearest_neighbor_dist(x) for x in range(num_clusters)]
            
            def s(x):
                k = kmeans.predict(x[np.newaxis, :])[0]
                return sk[k]
            
            def can_merge(g, h):
                for pg in g:
                    for ph in h:
                        vg = peaks[pg]
                        vh = peaks[ph]
                        dist_gh = np.linalg.norm(vg - vh)
                        
                        if max_tol(vg, vh) < self.tol and dist_gh / (s(vg) + s(vh)) <= self.merge_dist:
                            return True
                        
                return False
            
            while True:
                if len(groups) == 1:
                    break
                 
                # find closest mergable groups
                min_dist = np.inf
                for gi in range(len(groups)):
                    g = groups[gi]
                     
                    for hi in range(gi + 1, len(groups)):
                        h = groups[hi]
                         
                        if can_merge(g, h):
                            dist_gh = np.inf
                            for pg in g:
                                vg = peaks[pg]
                                for ph in h:
                                    vh = peaks[ph]
#                                     print("vg {} vh {}".format(vg, vh))
                                    dist_gh = min(dist_gh, 
                                                  np.linalg.norm(vg - vh))
                                     
                            if dist_gh < min_dist:
                                min_gi = gi
                                min_hi = hi
                                min_dist = dist_gh
                                 
                if min_dist == np.inf:
                    break
                 
                # merge the groups
                groups[min_gi].extend(groups[min_hi])
                for g in groups[min_hi]:
                    peak_groups[g] = min_gi
                del groups[min_hi]
                
            cluster_group = [0] * num_clusters
            cluster_peaks = [0] * num_clusters
    
            for gi, g in enumerate(groups):
                for p in g:
                    for cluster in peak_clusters[p]:
                        cluster_group[cluster] = gi
                        cluster_peaks[cluster] = p
    
            cluster_peak[data_group] = cluster_peaks
            self._cluster_group[data_group] = cluster_group    
            
        # we set this atomically to support appropriate updating of the GUI
        self._cluster_peak = cluster_peak
                                                 
         
    def apply(self, experiment):
        """
        Assign events to a cluster.
        
        Assigns each event to one of the k-means centroids from :meth:`estimate`,
        then groups together events in the same cluster hierarchy.
        
        Parameters
        ----------
        experiment : Experiment
            the :class:`.Experiment` to apply the gate to.
            
        Returns
        -------
        Experiment
            A new :class:`.Experiment` with the gate applied to it.  
            TODO - document the extra statistics
        """
 
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
         
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the gate's name "
                                       "before applying it!")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name))  
         
        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       "Experiment already has a column named {0}"
                                       .format(self.name))
         
        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")
            
        if not self._peaks:
            raise util.CytoflowOpError(None,
                                       "No model found.  Did you forget to "
                                       "call estimate()?")
 
        for c in self.channels:
            if c not in experiment.data:
                raise util.CytoflowOpError('channels',
                                           "Channel {0} not found in the experiment"
                                           .format(c))
                 
        for c in self.scale:
            if c not in self.channels:
                raise util.CytoflowOpError('scale',
                                           "Scale set for channel {0}, but it isn't "
                                           "in the experiment"
                                           .format(c))
        
        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                 
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True)
                 
        event_assignments = pd.Series(["{}_None".format(self.name)] * len(experiment), dtype = "object")
         
        # make the statistics       
#         clusters = [x + 1 for x in range(self.num_clusters)]
#           
#         idx = pd.MultiIndex.from_product([experiment[x].unique() for x in self.by] + [clusters] + [self.channels], 
#                                          names = list(self.by) + ["Cluster"] + ["Channel"])
#         centers_stat = pd.Series(index = idx, dtype = np.dtype(object)).sort_index()
                     
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError('by',
                                           "Group {} had no data"
                                           .format(group))
                
            if group not in self._kmeans:
                raise util.CytoflowOpError('by',
                                           "Group {} not found in the estimated "
                                           "model.  Do you need to re-run estimate()?"
                                           .format(group))
                
            x = data_subset.loc[:, self.channels[:]]
            
            for c in self.channels:
                x[c] = self._scale[c](x[c])
                 
            # which values are missing?
 
            x_na = pd.Series([False] * len(x))
            for c in self.channels:
                x_na[np.isnan(x[c]).values] = True
                         
            x = x.values
            x_na = x_na.values
            group_idx = groupby.groups[group]
            
            kmeans = self._kmeans[group]
  
            predicted_km = np.full(len(x), -1, "int")
            predicted_km[~x_na] = kmeans.predict(x[~x_na])
            
            groups = np.asarray(self._cluster_group[group])
            predicted_group = np.full(len(x), -1, "int")
            predicted_group[~x_na] = groups[ predicted_km[~x_na] ]
                 
            # outlier detection code.  this is disabled for the moment
            # because it is really slow.
                 
#             num_groups = len(set(groups))
#             if self.find_outliers:
#                 density = self._density[group]
#                 max_d = [-1.0 * np.inf] * num_groups
#                 
#                 for xi in range(len(x)):
#                     if x_na[xi]:
#                         continue
#                     
#                     x_c = predicted_group[xi]
#                     d_x_c = density(x[xi])
#                     if d_x_c > max_d[x_c]:
#                         max_d[x_c] = d_x_c
#                     
#                 group_density = [None] * num_groups
#                 group_weight = [0.0] * num_groups
#                 
#                 for c in range(num_groups):
#                     num_c = np.sum(predicted_group == c)
#                     clusters = np.argwhere(groups == c).flatten()
#                     
#                     normals = []
#                     weights = []
#                     for k in range(len(clusters)):
#                         num_k = np.sum(predicted_km == k)
#                         weight_k = num_k / num_c
#                         group_weight[c] += num_k / len(x)
#                         weights.append(weight_k)
#                         normals.append(self._normals[group][k])
#                         
#                     group_density[c] = lambda x, weights = weights, normals = normals: np.sum([w * n(x) for w, n in zip(weights, normals)], axis = 0)
# 
#                 for xi in range(len(x)):
#                     if x_na[xi]:
#                         continue
#                     
#                     x_c = predicted_group[xi]
#                     
#                     if density(x[xi]) / max_d[x_c] < 0.01:
#                         predicted_group[xi] = -1
#                         continue
#                     
#                     sum_d = 0
#                     for c in set(groups):
#                         sum_d += group_weight[c] * group_density[c](x[xi])
#                         
#                     if group_weight[x_c] * group_density[x_c](x[xi]) / sum_d < 0.8:
#                         predicted_group[xi] = -1
                        
#                     
#                     max_d = -1.0 * np.inf
#                     for x_c in x[predicted_group == c]:
#                         x_c_d = density(x_c)
#                         if x_c_d > max_d:
#                             max_d = x_c_d
#                             
#                     for i in range(len(x)):
#                         if predicted_group[i] == c and density(x[i]) / max_d <= 0.01:
#                             predicted_group[i] = -1
#                             
#                             
                    
            predicted_str = pd.Series(["(none)"] * len(predicted_group))
            for c in range(len(self._cluster_group[group])):
                predicted_str[predicted_group == c] = "{0}_{1}".format(self.name, c + 1)
            predicted_str[predicted_group == -1] = "{0}_None".format(self.name)
            predicted_str.index = group_idx
      
            event_assignments.iloc[group_idx] = predicted_str

        new_experiment = experiment.clone(deep = False)          
        new_experiment.add_condition(self.name, "category", event_assignments)
        
#         new_experiment.statistics[(self.name, "centers")] = pd.to_numeric(centers_stat)
 
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
        
        Parameters
        ----------
        channels : List(Str)
            Which channels to plot?  Must be contain either one or two channels.
            
        scale : List({'linear', 'log', 'logicle'})
            How to scale the channels before plotting them
            
        density : bool
            Should we plot a scatterplot or the estimated density function?
         
        Returns
        -------
        IView
            an IView, call :meth:`plot` to see the diagnostic plot.
        """
        channels = kwargs.pop('channels', self.channels)
        scale = kwargs.pop('scale', self.scale)
        density = kwargs.pop('density', False)
        
        for c in channels:
            if c not in self.channels:
                raise util.CytoflowViewError('channels',
                                             "Channel {} isn't in the operation's channels"
                                             .format(c))
                
        for s in scale:
            if s not in self.channels:
                raise util.CytoflowViewError('channels',
                                             "Channel {} isn't in the operation's channels"
                                             .format(s))

        for c in channels:
            if c not in scale:
                scale[c] = util.get_default_scale()
            
        if len(channels) == 0:
            raise util.CytoflowViewError('channels',
                                         "Must specify at least one channel for a default view")
        elif len(channels) == 1:
            v = FlowPeaks1DView(op = self)
            v.trait_set(channel = channels[0], 
                        scale = scale[channels[0]], 
                        **kwargs)
            return v
        
        elif len(channels) == 2:
            if density:
                v = FlowPeaks2DDensityView(op = self)
                v.trait_set(xchannel = channels[0], 
                            ychannel = channels[1],
                            xscale = scale[channels[0]],
                            yscale = scale[channels[1]], 
                            **kwargs)
                return v
            
            else:
                v = FlowPeaks2DView(op = self)
                v.trait_set(xchannel = channels[0], 
                            ychannel = channels[1],
                            xscale = scale[channels[0]],
                            yscale = scale[channels[1]], 
                            **kwargs)
                return v
        else:
            raise util.CytoflowViewError(None,
                                         "Can't specify more than two channels for a default view")
        
    
@provides(IView)
class FlowPeaks1DView(By1DView, AnnotatingView, HistogramView):
    """
    A one-dimensional diagnostic view for :class:`FlowPeaksOp`.  Plots a histogram
    of the channel, then overlays the k-means centroids in blue.

    Attributes
    ----------    

    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.flowpeaks1dview')
    friendly_id = Constant("1D FlowPeaks Diagnostic Plot")
    
    channel = Str
    scale = util.ScaleEnum
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        
        Parameters
        ----------
        
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
                
        view, trait_name = self._strip_trait(self.op.name)
        
        if self.channel in self.op._scale:
            scale = self.op._scale[self.channel]
        else:
            scale = util.scale_factory(self.scale, experiment, channel = self.channel)
    
        super(FlowPeaks1DView, view).plot(experiment,
                                          annotation_facet = self.op.name,
                                          annotation_trait = trait_name,
                                          annotations = self.op._kmeans,
                                          scale = scale,
                                          **kwargs)
        
        
    def _annotation_plot(self, axes, annotation, annotation_facet, 
                         annotation_value, annotation_color, **kwargs):
        
        kwargs.setdefault('orientation', 'vertical')

        if kwargs['orientation'] == 'horizontal':
            cidx = self.op.channels.index(self.channel)
            for k in range(0, self.op.num_clusters):
                c = self.op._scale[self.channel].inverse(annotation.cluster_centers_[k][cidx])
                plt.axhline(c, linewidth=3, color='blue')  
        else:
            cidx = self.op.channels.index(self.channel)
            for k in range(0, self.op.num_clusters):
                c = self.op._scale[self.channel].inverse(annotation.cluster_centers_[k][cidx])
                plt.axvline(c, linewidth=3, color='blue')  


     
class FlowPeaks2DView(By2DView, AnnotatingView, ScatterplotView):
    """
    A two-dimensional diagnostic view for :class:`FlowPeaksOp`.  Plots a 
    scatter-plot of the two channels, then overlays the k-means centroids in 
    blue and the clusters-of-k-means in pink.

    Attributes
    ----------

    """
     
    id = Constant('edu.mit.synbio.cytoflow.view.flowpeaks2dview')
    friendly_id = Constant("FlowPeaks 2D Diagnostic Plot")
    
    xchannel = Str
    ychannel = Str
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
 
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        
        Parameters
        ----------
        
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")

        annotations = {}
        for k in self.op._kmeans:
            annotations[k] = (self.op._kmeans[k], 
                              self.op._peaks[k], 
                              self.op._cluster_peak[k])
                
        view, trait_name = self._strip_trait(self.op.name)
        
        if self.xchannel in self.op._scale:
            xscale = self.op._scale[self.xchannel]
        else:
            xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)

        if self.ychannel in self.op._scale:
            yscale = self.op._scale[self.ychannel]
        else:
            yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
    
        super(FlowPeaks2DView, view).plot(experiment,
                                          annotation_facet = self.op.name,
                                          annotation_trait = trait_name,
                                          annotations = annotations,
                                          xscale = xscale,
                                          yscale = yscale,
                                          **kwargs)
 
    def _annotation_plot(self, 
                         axes, 
                         annotation, 
                         annotation_facet, 
                         annotation_value, 
                         annotation_color,
                         **kwargs):

        ix = self.op.channels.index(self.xchannel)
        iy = self.op.channels.index(self.ychannel)
        
        xscale = kwargs['xscale']
        yscale = kwargs['yscale']

        km = annotation[0]
        peaks = annotation[1]
        cluster_peak = annotation[2]
                 
        for k in range(len(km.cluster_centers_)):
            x = self.op._scale[self.xchannel].inverse(km.cluster_centers_[k][ix])
            y = self.op._scale[self.ychannel].inverse(km.cluster_centers_[k][iy])
                
            plt.plot(x, y, '*', color = 'blue')
                
            peak_idx = cluster_peak[k]
            peak = peaks[peak_idx]
            peak_x = xscale.inverse(peak[0])
            peak_y = yscale.inverse(peak[1])
                
            plt.plot([x, peak_x], [y, peak_y])
    
        for peak in peaks:
            x = self.op._scale[self.ychannel].inverse(peak[0])
            y = self.op._scale[self.xchannel].inverse(peak[1])
            plt.plot(x, y, 'o', color = "magenta")
                
                
class FlowPeaks2DDensityView(By2DView, AnnotatingView, NullView):
    """
    A two-dimensional diagnostic view for :class:`FlowPeaksOp`.  Plots the
    estimated density function of the two channels, then overlays the k-means 
    centroids in blue and the clusters-of-k-means in pink.

    Attributes
    ----------    
        
    """
     
    id = Constant('edu.mit.synbio.cytoflow.view.flowpeaks2ddensityview')
    friendly_id = Constant("FlowPeaks 2D Diagnostic Plot (Density)")
    
    xchannel = Str
    ychannel = Str
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    huefacet = Constant(None)
 
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        
        Parameters
        ----------
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")

        annotations = {}
        for k in self.op._kmeans:
            annotations[k] = (self.op._kmeans[k], 
                              self.op._peaks[k], 
                              self.op._cluster_peak[k])
        
        if self.xchannel in self.op._scale:
            xscale = self.op._scale[self.xchannel]
        else:
            xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)

        if self.ychannel in self.op._scale:
            yscale = self.op._scale[self.ychannel]
        else:
            yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
        
        if not self.op._kmeans:
            raise util.CytoflowViewError(None,
                                         "Must estimate a model before plotting "
                                         "the density plot.")
        
        for k in self.op._kmeans:
            annotations[k] = (self.op._kmeans[k], 
                              self.op._peaks[k], 
                              self.op._cluster_peak[k],
                              self.op._density[k])
                    
        super().plot(experiment,
                     annotations = annotations,
                     xscale = xscale,
                     yscale = yscale,
                     **kwargs)
        
    def _grid_plot(self, experiment, grid, **kwargs):
        # all the real plotting happens in _annotation_plot.  this just sets some
        # defaults and then stores them for later.

        kwargs.setdefault('antialiased', False)
        kwargs.setdefault('linewidth', 0)
        kwargs.setdefault('edgecolors', 'face')
        kwargs.setdefault('shading', 'auto')
        kwargs.setdefault('cmap', plt.get_cmap('viridis'))
        
        xscale = kwargs['scale'][self.xchannel]
        xlim = kwargs['lim'][self.xchannel]
        yscale = kwargs['scale'][self.ychannel]
        ylim = kwargs['lim'][self.ychannel]
        
        # can't modify colormaps in place
        cmap = copy.copy(kwargs['cmap'])
        
        under_color = kwargs.pop('under_color', None)
        if under_color is not None:
            cmap.set_under(color = under_color)
        else:
            cmap.set_under(color = cmap(0.0))

        bad_color = kwargs.pop('bad_color', None)
        if bad_color is not None:
            cmap.set_bad(color = cmap(0.0))
        
        gridsize = kwargs.pop('gridsize', 50)
        xbins = xscale.inverse(np.linspace(xscale(xlim[0]), xscale(xlim[1]), gridsize))
        ybins = yscale.inverse(np.linspace(yscale(ylim[0]), yscale(ylim[1]), gridsize))
            
        for (i, j, _), _ in grid.facet_data():
            ax = grid.facet_axis(i, j)
            ax.fp_xbins = xbins
            ax.fp_ybins = ybins
            ax.fp_keywords = kwargs

        super()._grid_plot(experiment, grid, **kwargs)
            
        return dict(xscale = xscale,
                    xlim = xlim,
                    yscale = yscale,
                    ylim = ylim,
                    cmap = kwargs['cmap'])
 
    def _annotation_plot(self, axes, annotation, annotation_facet, 
                         annotation_value, annotation_color, **kwargs):

        km = annotation[0]
        peaks = annotation[1]
        cluster_peak = annotation[2]
        density = annotation[3]
        
        xbins = axes.fp_xbins
        ybins = axes.fp_ybins
        kwargs = axes.fp_keywords

        # get rid of some kwargs that confuse pcolormesh
        kwargs.pop('annotations', None)
        kwargs.pop('annotation_facet', None)
        kwargs.pop('plot_name', None)
        
        xscale = kwargs['scale'][self.xchannel]
        yscale = kwargs['scale'][self.ychannel]
        
        kwargs.pop('scale')
        kwargs.pop('lim')
        
        smoothed = kwargs.pop('smoothed', False)
        smoothed_sigma = kwargs.pop('smoothed_sigma', 1)

        h = density(util.cartesian([xscale(xbins), yscale(ybins)]))
        h = np.reshape(h, (len(xbins), len(ybins)))
        if smoothed:
            h = scipy.ndimage.filters.gaussian_filter(h, sigma = smoothed_sigma)
        axes.pcolormesh(xbins, ybins, h.T, **kwargs)

        ix = self.op.channels.index(self.xchannel)
        iy = self.op.channels.index(self.ychannel)
                 
        for k in range(len(km.cluster_centers_)):

            x = self.op._scale[self.xchannel].inverse(km.cluster_centers_[k][ix])
            y = self.op._scale[self.ychannel].inverse(km.cluster_centers_[k][iy])
                
            plt.plot(x, y, '*', color = 'blue')
                
            peak_idx = cluster_peak[k]
            peak = peaks[peak_idx]
            peak_x = xscale.inverse(peak[0])
            peak_y = yscale.inverse(peak[1])
                
            plt.plot([x, peak_x], [y, peak_y])
    
        for peak in peaks:
            x = self.op._scale[self.ychannel].inverse(peak[0])
            y = self.op._scale[self.xchannel].inverse(peak[1])
            plt.plot(x, y, 'o', color = "magenta")   

util.expand_class_attributes(FlowPeaks1DView)
util.expand_method_parameters(FlowPeaks1DView, FlowPeaks1DView.plot)

util.expand_class_attributes(FlowPeaks2DView)
util.expand_method_parameters(FlowPeaks2DView, FlowPeaks2DView.plot)

util.expand_class_attributes(FlowPeaks2DDensityView)
util.expand_method_parameters(FlowPeaks2DDensityView, FlowPeaks2DDensityView.plot)
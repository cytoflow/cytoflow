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
cytoflow.operations.hdbscan
--------------------------

Use Hierarchical Density-Based Spatial Clustering of Applications
 with Noise clustering to cluster events in any number of dimensions.
`hdbscan` has one class:

`HDBSCANOp` -- the `IOperation` to perform the clustering.
"""


from traits.api import (HasStrictTraits, Str, Dict, Any, Instance,
                        Constant, List, provides)

import numpy as np

import pandas as pd
import hdbscan

import cytoflow.utility as util

from .i_operation import IOperation


@provides(IOperation)
class HDBSCANOp(HasStrictTraits):
    """
    Use a HDBSCAN clustering algorithm to cluster events.  

    Call `estimate` to compute the cluster centroids.

    Calling `apply` creates a new categorical metadata variable 
    named `name`, with possible values ``{name}_1`` .... ``name_n`` where 
    ``n`` is the number of clusters, specified with `num_clusters`.

    The same model may not be appropriate for different subsets of the data set.
    If this is the case, you can use the `by` attribute to specify 
    metadata by which to aggregate the data before estimating (and applying) a 
    model.  The  number of clusters is the same across each subset, though.

    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column

    channels : List(Str)
        The channels to apply the clustering algorithm to.

    scale : Dict(Str : {"linear", "logicle", "log"})
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in `channels` but not in `scale`, the current 
        package-wide default (set with `set_default_scale`) is used.

        .. note::
           Sometimes you may see events labeled ``{name}_None`` -- this results 
           from events for which the selected scale is invalid. For example, if
           an event has a negative measurement in a channel and that channel's
           scale is set to "log", this event will be set to ``{name}_None``.

    min_cluster_size : int, optional (default=5)
        The minimum size of clusters; single linkage splits that contain
        fewer points than this will be considered points "falling out" of a
        cluster rather than a cluster splitting into two new clusters.

    min_samples : int, optional (default=None)
        The number of samples in a neighbourhood for a point to be
        considered a core point.

    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting `by` to ``["Time", "Dox"]`` will 
        fit the model separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
    """

    id = Constant('edu.mit.synbio.cytoflow.operations.hdbscan')
    friendly_id = Constant("HDBSCAN Clustering")

    name = Str
    channels = List(Str)
    scale = Dict(Str, util.ScaleEnum)
    min_cluster_size = util.PositiveInt(5, allow_zero=False)
    min_samples = util.PositiveInt(None, allow_none = True, allow_zero=False)
    by = List(Str)

    _hdbclusters = Dict(Any, Instance(hdbscan.HDBSCAN), transient=True)
    _scale = Dict(Str, Instance(util.IScale), transient=True)

    def estimate(self, experiment, subset=None):
        """
        Estimate the HDBSCAN clusters

        Parameters
        ----------
        experiment : Experiment
            The `Experiment` to use to estimate the HDBSCAN clusters

        subset : str (default = None)
            A Python expression that specifies a subset of the data in 
            ``experiment`` to use to parameterize the operation.
        """

        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")

        if self.min_cluster_size < 2:
            raise util.CytoflowOpError('min_cluster_size',
                                       "min_cluster_size must be >= 2")

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
            if b not in experiment.data:
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
        self._scale = util.init_channel_scales(experiment, self.channels, self.scale)

        hdbclusters = {}
        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError('by',
                                           "Group {} had no data"
                                           .format(group))
            x = data_subset.loc[:, self.channels[:]]
            for c in self.channels:
                x[c] = self._scale[c](x[c])

            # drop data that isn't in the scale range
            for c in self.channels:
                x = x[~(np.isnan(x[c]))]
            x = x.values

            hdbclusters[group] = hdbc = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size, min_samples=self.min_samples, prediction_data=True)

            hdbc.fit(x)

        # do this so the UI can pick up that the estimate changed
        self._hdbclusters = hdbclusters

    def apply(self, experiment):
        """
        Apply the Hdbscan clustering to the data.

        Returns
        -------
        Experiment
            a new Experiment with one additional entry in `Experiment.conditions` 
            named `name`, of type ``category``.  The new category has 
            values  ``name_1``, ``name_2``, etc to indicate which hdbscan cluster 
            an event is a member of.
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

        if not self._hdbclusters:
            raise util.CytoflowOpError(None,
                                       "No components found.  Did you forget to "
                                       "call estimate()?")

        if len(self.channels) == 0:
            raise util.CytoflowOpError('channels',
                                       "Must set at least one channel")

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
            if b not in experiment.data:
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

        event_assignments = pd.Series(["{}_None".format(self.name)]
                                      * len(experiment), dtype="object")

        for group, data_subset in groupby:
            if len(data_subset) == 0:
                raise util.CytoflowOpError('by',
                                           "Group {} had no data"
                                           .format(group))

            if group not in self._hdbclusters:
                raise util.CytoflowOpError('by',
                                           "Group {} not found in the estimated model. "
                                           "Do you need to re-run estimate()?"
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

            clusterer = self._hdbclusters[group]

            predicted = np.full(len(x), -1, "int")
            predicted_labels, _ = hdbscan.approximate_predict(clusterer,x[~x_na])
            predicted[~x_na] = predicted_labels

            predicted_str = pd.Series(["(none)"] * len(predicted))

            for c in np.unique(predicted):
                predicted_str[predicted == c] = "{0}_{1}".format(self.name, c + 1)
            predicted_str[predicted == -1] = "{0}_None".format(self.name)
            predicted_str.index = group_idx

            event_assignments.iloc[group_idx] = predicted_str

        new_experiment = experiment.clone(deep=False)
        new_experiment.add_condition(self.name, "category", event_assignments)

        new_experiment.history.append(self.clone_traits(transient=lambda _: True))
        return new_experiment

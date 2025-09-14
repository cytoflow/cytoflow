#!/usr/bin/env python3.11
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2025
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
cytoflow.views.mst
------------------

Plots a minimum spanning tree of a statistic. Particularly useful for
visualizing the results of a clustering operations such as `KMeansOp`
and `SOMOp`. 

`MSTView` -- plots the minimum spanning tree.
"""

import math
from warnings import warn
from natsort import natsorted

from traits.api import HasStrictTraits, provides, Enum, Str, Callable, Constant, \
                       List, Float, Int
import seaborn as sns
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy.spatial.distance
import igraph
import numpy as np

import cytoflow
import cytoflow.utility as util

from .i_view import IView


@provides(IView)
class MSTView(HasStrictTraits):
    """
    A view that creates a minimum spanning tree view of a statistic. 
    
    Set `statistic` to the name of the statistic to plot; set `feature` to the name
    of that statistic's feature you'd like to analyze. Then, set `locations` to
    *another* statistic whose features are the locations (in any number of dimensions)
    of the nodes in the tree -- usually these are cluster centroids from `KMeansOp`
    or `SOMOp` (see the example below). The view computes a minimum-spanning tree 
    containing the nodes and lays it out in two dimensions.
    
    There are three different ways of plotting the value at each location in tree: 
    
    * Setting `style` to ``heat`` (the default) will produce an MST with a circle 
      at each vertex and the color of the circle is related to the intensity of 
      the value of `feature`. (In this scenario, `variable` is ignored.)
      
    * Setting `style` to ``pie`` will draw a pie plot at each location. If 
      `variable` is set, then the values of `variable` are used as the categories
      of the pie, and the arc length of each slice of pie is related 
      to the intensity of the value of `feature`. If `variable` is unset, then
      `feature` is ignored and the *features* of the statistic are used as the
      categories.
      
    * Setting `style` to ``petal`` will draw a "petal plot" in each cell. If 
      `variable` is set, then the values of `variable` are used as the categories, 
      but unlike a pie plot, the arc width of each slice is equal. Instead, the 
      radius of the pie slice scales with the square root of the intensity, so 
      that the relationship between area and intensity remains the same. If 
      `variable` is unset, then `feature` is ignored and the *features* of the
      statistic are used as the categories.
      
    .. warning::
        If `style` is ``pie`` or ``petal``, then negative data will be clipped
        to 0! 
      
    Optionally, you can set `size_function` to scale the circles (or pies or petals)
    by a function computed on `Experiment.data`. (Often set to ``len`` to scale 
    by the number of events in each cluster.)
    
    .. note::
       If you'd like to *select* events based on this view (by drawing a 
       polygon around the nodes of the tree), you can do that with
       `SOMOp`.
    
    Attributes
    ----------
        
    statistic : Str
        The statistic to plot. Must be a key in `Experiment.statistics`.
        
    locations : Str
        A statistic whose levels are the same as `statistic` and whose features
        are the dimensions of the locations of each node to plot.
        
    .. note:: If `style` is ``heat``, then the levels of `statistic` must be the
              same as the levels of `locations`. If `style` is ``pie`` or ``petal``,
              the levels of `statistic` must be the levels of `locations` plus `variable`.
        
    locations_level : Str
        Which level in the `locations` statistic is different at each location? 
        The values of the others must be specified in the ``plot_name`` parameter 
        of `plot`.  Optional if there is only one level in `locations`.
        
    locations_features : List(Str)
        Which features in `locations` to use. By default, use all of them. 
        
    .. warning::
        The `KMeansOp` statistic is mostly locations, but also has the a 
        **Proportion** feature. You likely don't want to use it as a location 
        for laying out the minimum spanning tree!
            
    variable : Str
        The variable used for plotting pie and petal plots. Must be left empty
        for a heatmap.
        
    feature : Str
        The column in the statistic to plot (often a channel name.)
        
    style : Enum(``heat``, ``pie``, ``petal``) (default = ``heat``)
        What kind of plot to make?
        
    scale : {'linear', 'log', 'logicle'}
        For a heat map, how should the color of `feature` be scaled before 
        plotting? For pie and petal maps, how should the input data be normalized
        to [0,1] before plotting?
                
    size_function : Callable (default: None)
        If set, separate the `Experiment` into subsets by levels of `locations`, 
        compute a function on them, and scale the size of each tree node by 
        those values. The callable should take a single `pandas.DataFrame` 
        argument and return a *positive* ``float`` or value that can be cast to
        ``float`` (such as ``int``).  Of particular use is ``len``, which will
        scale the cells by the number of events in each subset.
        
    metric : Str (default: ``euclidean``)
        What metric should be used to compute distance in the tree? Must be one
        of ``braycurtis``, ``canberra``, ``chebyshev``, ``cityblock``, ``correlation``, 
        ``cosine``, ``dice``, ``euclidean``, ``hamming``, ``jaccard``, ``jensenshannon``, 
        ``kulczynski1``, ``mahalanobis``, ``matching``, ``minkowski``, ``rogerstanimoto``, 
        ``russellrao``, ``seuclidean``, ``sokalmichener``, ``sokalsneath``, ``sqeuclidean``, 
        ``yule``. Suggestion: use ``euclidean`` for small numbers of dimensions 
        (location features) and ``cosine`` for larger numbers.
        
    subset : str
        An expression that specifies the subset of the statistic to plot.
        Passed unmodified to `pandas.DataFrame.query`.
        
    Note
    ----
    `MSTView` is *not* a subclass of `BaseView` or any of its descendants.
    It implements the `IView` interface but does it does not use 
    `seaborn.FacetGrid` for laying out its plots.
    

    Examples
    --------
    
    Make a little data set.
    
    .. plot::
        :context: close-figs
            
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
        
    Compute some KMeans clusters
    
    .. plot::
        :context: close-figs
        
        >>> km = flow.KMeansOp(name = "KMeans",
        ...                    channels = ["V2-A", "Y2-A", "B1-A"],
        ...                    scale = {"V2-A" : "logicle",
        ...                             "Y2-A" : "logicle",
        ...                             "B1-A" : "logicle"},
        ...                    num_clusters = 20)       
        >>> km.estimate(ex)
        >>> ex2 = km.apply(ex)
        
    Add a statistic
    
    .. plot::
        :context: close-figs

        >>> ex3 = flow.ChannelStatisticOp(name = "ByDox",
        ...                               channel = "Y2-A",
        ...                               by = ["KMeans", "Dox"],
        ...                               function = len).apply(ex2) 
    
    Plot the minimum spanning tree
    
    .. plot::
        :context: close-figs
        
        >>> flow.MSTView(statistic = "ByDox", 
        ...              locations = "KMeans", 
        ...              locations_features = ["V2-A", "Y2-A", "B1-A"],
        ...              feature = "Y2-A",
        ...              variable = "Dox",
        ...              style = "pie").plot(ex3)
    
    """
    
    id = Constant("cytoflow.view.mst")
    friendly_id = Constant("Minimum Spanning Tree") 
    
    statistic = Str
    locations = Str
    locations_level = Str
    locations_features = List(Str)
    variable = Str
    feature = Str
    scale = util.ScaleEnum
    style = Enum("heat", "pie", "petal")
    metric = Str("euclidean")
    subset = Str
    
    size_function = Callable
    
    # bits to support the interactive selector for MSTOp
    _loc_level = Str
    _vertices = List(List(Float))
    _groups = List(Int)
    
    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot a chart of a variable's values against a statistic.
        
        Parameters
        ----------
        experiment: Experiment
            The `Experiment` to plot using this view.
            
        plot_name : str
            If this `IView` can make multiple plots, ``plot_name`` is
            the name of the plot to make.  Must be one of the values retrieved
            from `enum_plots`.
            
        title : str
            Set the plot title
            
        legend : bool
            Plot a legend or color bar?  Defaults to `True`.
            
        legendlabel : str
            Set the label for the color bar or legend
 
        palette : palette name
            Colors to use for the different levels of the hue variable. 
            Should be something that can be interpreted by
            `seaborn.color_palette`. If plotting a heat map, this should be
            a continuous color map ('viridis' is the default.) Otherwise,
            choose either a discrete color map ('deep' is the default) or
            a continuous color map from which equi-spaced colors will be drawn.
            
        radius : float
            The radius of the circle or pie plots, on a scale from 0 to 1.
            
        All other parameters are passed to the `matplotlib.patches.Circle` or
        `matplotlib.patches.Wedge` construtors (ie, they should be patch attributes).

        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
        
        if self.style == "heat" and self.variable != "":
            raise util.CytoflowViewError("variable",
                                         "If `style` is \"heat\", `variable` must be empty!")
        
        stat = self._get_stat(experiment)
        locs = self._get_locs(experiment)
        
        stat = self._subset_data(self.statistic, stat)
        locs = self._subset_data(self.locations, locs)
        experiment_data = experiment.data
        
        # if not self.feature:
        #     raise util.CytoflowViewError('feature',
        #                                  "Must set `feature` to a feature in `statistic`")
        #
        # # the indices of `stat` and `locs` may have the same levels, or the index 
        # # of `stat` may have one more -- if so, it must be `self.variable`. to get
        # # things compatible, we'll re-order the index levels of stats.
        # locs_names = set(stat.index.names) - set([self.variable]) if self.variable else set(stat.index.names)
        # if locs_names != set(locs.index.names):
        #     if self.style == "heat":
        #         raise util.CytoflowViewError('locations',
        #                                      "If `style` is \"heat\", the levels of 'locations' must be the same as levels of 'statistic'")
        #     else:
        #         raise util.CytoflowViewError('locations',
        #                                      "If `style` is not \"heat\", then the levels of 'locations' must be the same as the levels of 'statistic' without 'variable'.")
        #
        # # need to re-index stat to be compatible with locs
        # stat_names = locs.index.names + [self.variable] if self.variable else locs.index.names
        # new_stat_idx = stat.index.reorder_levels(stat_names)
        # stat = stat.copy()
        # stat.index = new_stat_idx
        #
        # # gotta remove rows of stat that aren't in locs
        # # (because some clustering add a -1 value
        # stat_idx = stat.index.droplevel(self.variable) if self.variable else stat.index
        # stat = stat[[v in locs.index for v in stat_idx]]
        #
        # if stat.empty:
        #     raise util.CytoflowViewError('locations',
        #                                  f'{self.statistic} and {self.locations} dont share any rows!')
        #
        # # do we have to get a plot_name?
        # if len(locs_names) > 1 and not self.locations_level:
        #     raise util.CytoflowViewError('location_level',
        #                                  'If `locations` has more than one index level, you must set `location_level`.')
        #
        # if self.locations_level and self.locations_level not in locs_names:
        #     raise util.CytoflowViewError('location_level',
        #                                  '`location_level` value {} is not in {}'
        #                                  .format(self.locations_level, self.ocations))
        #
        # self._loc_level = loc_level = self.locations_level if self.locations_level else list(locs_names)[0]            
        # unused_names = list(set(locs_names) - set([loc_level]))
        
        if locs.index.nlevels > 1:
            if not self.locations_level:
                raise util.CytoflowViewError('locations_level',
                                             "If 'locations' has more than one level, "
                                             "'locations_level' must be set!")

            if self.locations_level not in locs.index.names:
                raise util.CytoflowViewError('locations_level',
                                             "'locations_level' must be a level in 'locations'")
                
            if self.locations_level not in stat.index.names:
                raise util.CytoflowViewError('locations_level',
                                             "'locations_level' must be a level in 'statistic'")
            
            locations_level = self.locations_level
        else:
            locations_level = locs.index.names[0]
            
            if locations_level not in stat.index.names:
                raise util.CytoflowViewError(f"{locations_level} is the only level in 'locations', but it's not in 'statistic'")
            
        self._loc_level = locations_level
        unused_locs_levels = set(locs.index.names) - set([locations_level])
        unused_stat_levels = set(stat.index.names) - set([locations_level])
        
        if self.style == "heat":
            if not self.feature:
                raise util.CytoflowViewError('feature',
                                             "For style 'heat', you must set 'feature'!")
            
            if self.feature not in stat.columns:
                raise util.CytoflowViewError('feature',
                                             "Can't find feature '{}' in the statistic columns."
                                             .format(self.feature))

            
        if self.style != "heat":
            if self.variable:
                if self.variable not in stat.index.names:
                    raise util.CytoflowViewError('variable',
                                                 "Can't find variable '{}' in the statistic index."
                                                 .format(self.variable))
            
                if not self.feature:
                    raise util.CytoflowViewError('feature',
                                                 "For styles 'pie' and 'petal', if you set 'variable', you must set 'feature'!"
                                                 .format(self.variable))
                
                if self.feature not in stat.columns:
                    raise util.CytoflowViewError('feature',
                                                 "Can't find feature '{}' in the statistic columns."
                                                 .format(self.feature))
            
                unused_stat_levels -= set([self.variable])
                
        if unused_locs_levels != unused_stat_levels:
            if self.style != "heat" and self.variable:
                raise util.CytoflowViewError('locations',
                                             f"After removing 'variable' {self.variable}, unused levels in 'statistic' are {unused_stat_levels}; unused levels in 'locations' are {unused_locs_levels}. They should be the same!")
            else:
                raise util.CytoflowViewError('locations',
                                             f"Unused levels in 'statistic' are {unused_stat_levels}; unused levels in 'locations' are {unused_locs_levels}. They should be the same!")

            
        # need to re-index stat to be compatible with locs
        stat_names = locs.index.names + [self.variable] if self.variable else locs.index.names
        new_stat_idx = stat.index.reorder_levels(stat_names)
        stat = stat.copy()
        stat.index = new_stat_idx
        
        # gotta remove rows of stat that aren't in locs
        # (because some clustering add a -1 value
        stat_idx = stat.index.droplevel(self.variable) if self.variable else stat.index
        stat = stat[[v in locs.index for v in stat_idx]]

        if plot_name is not None and not unused_stat_levels:
            raise util.CytoflowViewError('plot_name',
                                         "You specified a plot name, but all "
                                         "the index levels of `locations` are already used")
        
        if unused_stat_levels:
            stat_groupby = stat.groupby(list(unused_stat_levels), observed = True)
            locs_groupby = locs.groupby(list(unused_stat_levels), observed = True)

            if plot_name is None:
                raise util.CytoflowViewError('plot_name',
                                             "You must use names {} in the plot name. "
                                             "Possible plot names: {}"
                                             .format(unused_stat_levels, list(stat_groupby.groups.keys())))

            if plot_name not in set(stat_groupby.groups.keys()):
                raise util.CytoflowViewError('plot_name',
                                             "Plot {} is invalid; must  be one of {}"
                                             .format(plot_name, list(stat_groupby.groups.keys())))
                
            stat = stat_groupby.get_group(plot_name if util.is_list_like(plot_name) else (plot_name,))
            locs = locs_groupby.get_group(plot_name if util.is_list_like(plot_name) else (plot_name,))
            if self.size_function:
                experiment_data = experiment.data.groupby(unused_stat_levels, observed = True).get_group(plot_name if util.is_list_like(plot_name) else (plot_name,))
        
        title = kwargs.pop("title", None)
        legend = kwargs.pop('legend', True)
        legendlabel = kwargs.pop('legendlabel', self.variable)
                
        if cytoflow.RUNNING_IN_GUI:
            sns_style = kwargs.pop('sns_style', 'whitegrid')
            sns_context = kwargs.pop('sns_context', 'notebook')
            sns.set_style(sns_style)
            sns.set_context(sns_context)
        else:
            if 'sns_style' in kwargs:
                kwargs.pop('sns_style')
                warn("'sns_style' is ignored when not running in the GUI. Feel free to change the seaborn global settings.",
                     util.CytoflowViewWarning)
                
            if 'sns_context' in kwargs:
                kwargs.pop('sns_context')
                warn("'sns_context' is ignored when not running in the GUI. Feel free to change the seaborn global settings.",
                     util.CytoflowViewWarning)
                
        if self.size_function:
            group_scale = {}
            s_max = 0.0
            for group_name, group_data in experiment_data.groupby(by = list(locs.index.names), observed = True):
                if group_name not in locs.index:
                    continue
                
                s = self.size_function(group_data)
                try:
                    s = float(s)
                except Exception as e:
                    raise util.CytoflowViewError('size_function',
                                                 'Called size_function on group {} and return type was {}; must return a float!'
                                                 .format(group_name, type(s))) from e
                                                 
                if s < 0.0:
                    raise util.CytoflowViewError('size_function',
                                                 'Called size_function on group {} and return was {}; must be >0!'
                                                 .format(group_name, s))
                if s > s_max:
                    s_max = s
                group_scale[group_name] = s
                
            group_scale = {k : v / s_max for k, v in group_scale.items()}
        
        # set up the data normalizer
        if 'norm' not in kwargs:
            data_scale = util.scale_factory(scale = self.scale,
                                            experiment = experiment,
                                            statistic = self.statistic,
                                            features = [self.feature] 
                                                       if self.feature 
                                                       else list(stat.columns))
            data_norm = data_scale.norm()
        else:
            data_norm = kwargs.pop('norm')
                    
        # find the locations for the groups
        # MST logic: https://github.com/saeyslab/FlowSOM_Python/blob/d8cb6a5934b1ca9c82f4bba27a1f3cd9862a0596/src/flowsom/main.py#L255
        
        # compute the all-pairs distances
        locs_values = locs[self.locations_features].values if self.locations_features else locs.values
        adjacency_graph = scipy.spatial.distance.cdist(locs_values, locs_values, self.metric)
        
        # create a fully-connected graph
        full_graph = igraph.Graph.Weighted_Adjacency(adjacency_graph, mode = "undirected", loops = False)
        
        # normalize the edge weights (necessary??)
        # mst_graph.es["weight"] = mst_graph.es["weight"] / np.mean(mst_graph.es["weight"]) 
        
        # create the spanning tree
        mst_graph = igraph.Graph.spanning_tree(full_graph, weights = full_graph.es["weight"])
        
        # normalize the edge weights (necessary??)
        mst_graph.es["weight"] = mst_graph.es["weight"] / np.mean(mst_graph.es["weight"]) 
        
        # optimize the layout for plotting
        layout = mst_graph.layout_kamada_kawai(seed = mst_graph.layout_grid(),
                                               maxiter = 50 * mst_graph.vcount(),
                                               kkconst = max([mst_graph.vcount(), 1]))
        layout.fit_into((0.05, 0.05, 0.95, 0.95))

        # make the new figure
        fig = plt.figure()
        ax = fig.add_subplot(111)

        # plot the edges connecting nodes
        segments = [[layout.coords[edge[0]], layout.coords[edge[1]]] for edge in mst_graph.get_edgelist()]
        segments = mpl.collections.LineCollection(segments, zorder = 1)
        segments.set_edgecolor("black")
        ax.add_collection(segments)
        
        # save the locations for MSTOp
        self._groups = list(stat.groupby(locations_level, observed = True).groups.keys())
        self._vertices = layout.coords
        
        # now, plot the patches
        
        # since the edge length is uniform (i thiiiiink?), set the radii of the patches
        # to 1/3 of the edge length.
        edge_len = scipy.spatial.distance.euclidean(layout.coords[mst_graph.get_edgelist()[0][0]],
                                                    layout.coords[mst_graph.get_edgelist()[0][1]])
        
        radius = kwargs.pop('radius', edge_len * 0.4)
        if radius < 0 or radius > 1:
            raise util.CytoflowViewError('radius',
                                         'Radius must be between 0 and 1.')
                
        if self.style == "heat":
            cmap_name = kwargs.pop('palette', 'viridis')
            cmap = sns.color_palette(cmap_name, as_cmap = True)
            if isinstance(cmap, list):
                raise util.CytoflowViewError('palette',
                                             "{} is a qualitative (discrete) palette. Choose a continuous one such as 'rocket', 'mako' or 'viridis'")
                  
            patches = []  
            for idx, x in enumerate(stat[self.feature]):
                patch = mpl.patches.Circle(xy = layout.coords[idx], 
                                           radius = radius, 
                                           facecolor = cmap(data_norm(x)),
                                           clip_on = False)
                if self.size_function:
                    patch.set_radius(radius * group_scale[locs.index.to_flat_index()[idx]])
                    
                patch.set(**kwargs)
                    
                patches.append(patch)

            ax.add_collection(mpl.collections.PatchCollection(patches, match_original = True))
                                
            if legend:
                plt.colorbar(mpl.cm.ScalarMappable(norm = data_norm, cmap = cmap),
                             ax = ax,
                             label = legendlabel)

        elif self.style == "pie":
            if self.variable:
                variable_values = list(stat.index.get_level_values(self.variable).unique())
            else:
                variable_values = list(stat.columns)
                
            palette_name = kwargs.pop('palette', 'deep')
            palette = sns.color_palette(palette_name, n_colors = len(variable_values))
            colors = {var: palette[vi] for vi, var in enumerate(variable_values)}
            
            groups = stat.groupby(locations_level, observed = True)
            legend_artists = {}

            for idx, group in groups:
                loc = layout.coords[idx]
                if self.variable:
                    group_data = group[self.feature]
                else:
                    assert(len(group) == 1)
                    group_data = group.iloc[0]
                    
                normed_data = group_data.apply(data_norm)
                normed_data /= normed_data.sum()
                
                theta1 = 0
                for frac_idx, frac in enumerate(normed_data):
                    theta2 = theta1 + frac
                    
                    if self.variable:
                        label = group.index.get_level_values(self.variable).values[frac_idx]
                    else:
                        label = group_data.index[frac_idx]
                        
                    color = colors[label]
                    w = mpl.patches.Wedge(center = loc, 
                                          r = radius, 
                                          theta1 = 360 * theta1, 
                                          theta2 = 360 * theta2, 
                                          facecolor = color,
                                          edgecolor = 'white',
                                          label = label,
                                          clip_on = False)
                        
                    if self.size_function:
                        w.set_radius(w.r * group_scale[locs.index.to_flat_index()[idx]])
                        
                    w.set(**kwargs)
                        
                    ax.add_artist(w)
                    if label not in legend_artists:
                        legend_artists[label] = w
                    theta1 = theta2
                            
            if(legend):
                legend_artists = {k: legend_artists[k] for k in natsorted(legend_artists.keys())}
                ax.legend(handles = legend_artists.values(), 
                          title = legendlabel)
                
        elif self.style == "petal":
            if self.variable:
                variable_values = list(stat.index.get_level_values(self.variable).unique())
            else:
                variable_values = list(stat.columns)
                
            num_wedges = len(variable_values)
            palette_name = kwargs.pop('palette', 'deep')
            palette = sns.color_palette(palette_name, n_colors = len(variable_values))
            colors = {var: palette[vi] for vi, var in enumerate(variable_values)}
            wedge_theta = 360 / num_wedges
        
            groups = stat.groupby(locations_level, observed = True)
            legend_artists = {}
        
            for idx, group in groups:
                loc = layout.coords[idx]
                if self.variable:
                    group_data = group[self.feature]
                else:
                    assert(len(group) == 1)
                    group_data = group.iloc[0]
                    
                normed_data = group_data.apply(data_norm)
                normed_data /= normed_data.max()
        
                theta1 = 0
                for label in variable_values:
                    theta2 = theta1 + wedge_theta
                    
                    if self.variable:
                        if label in group.index.get_level_values(self.variable):
                            frac = normed_data.xs(level = self.variable, key = label).iloc[0]
                        else:
                            frac = 0
                    else:
                        frac = normed_data.loc[label]
        
                    r = radius * math.sqrt(frac)
                    color = colors[label]
                    w = mpl.patches.Wedge(center = loc, 
                                          r = r, 
                                          theta1 = theta1, 
                                          theta2 = theta2, 
                                          label = label,
                                          facecolor = color,
                                          edgecolor = 'white',
                                          clip_on = False)
        
                    if self.size_function:
                        w.set_radius(w.r * group_scale[locs.index.to_flat_index()[idx]])
        
                    w.set(**kwargs)
        
                    ax.add_artist(w)
                    if label not in legend_artists:
                        legend_artists[label] = w
                    theta1 = theta2
        
            if(legend):
                legend_artists = {k: legend_artists[k] for k in natsorted(legend_artists.keys())}
                ax.legend(handles = legend_artists.values(),
                          title = legendlabel)    
        
        # make axes equal (spacing)
        ax.axis('equal')
        ax.set_axis_off()
        
        if title:
            plt.suptitle(title, y = 1.02)
            
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

        stat = self._get_stat(experiment)
        locs = self._get_locs(experiment)
                
        stat = self._subset_data(self.statistic, stat)
        locs = self._subset_data(self.locations, locs)
        
        if locs.index.nlevels > 1:
            if not self.locations_level:
                raise util.CytoflowViewError('locations_level',
                                             "If 'locations' has more than one level, "
                                             "'locations_level' must be set!")

            if self.locations_level not in locs.index.names:
                raise util.CytoflowViewError('locations_level',
                                             "'locations_level' must be a level in 'locations'")
                
            if self.locations_level not in stat.index.names:
                raise util.CytoflowViewError('locations_level',
                                             "'locations_level' must be a level in 'statistic'")
            
            locations_level = self.locations_level
        else:
            locations_level = locs.index.names[0]
            
            if locations_level not in stat.index.names:
                raise util.CytoflowViewError(f"{locations_level} is the only level in 'locations', but it's not in 'statistic'")
            
        unused_locs_levels = set(locs.index.names) - set([locations_level])
        unused_stat_levels = set(stat.index.names) - set([locations_level])
        
        if self.style == "heat":
            if not self.feature:
                raise util.CytoflowViewError('feature',
                                             "For style 'heat', you must set 'feature'!")
            
            if self.feature not in stat.columns:
                raise util.CytoflowViewError('feature',
                                             "Can't find feature '{}' in the statistic columns."
                                             .format(self.feature))

            
        if self.style != "heat":
            if self.variable:
                if self.variable not in stat.index.names:
                    raise util.CytoflowViewError('variable',
                                                 "Can't find variable '{}' in the statistic index."
                                                 .format(self.variable))
            
                if not self.feature:
                    raise util.CytoflowViewError('feature',
                                                 "For styles 'pie' and 'petal', if you set 'variable', you must set 'feature'!"
                                                 .format(self.variable))
                
                if self.feature not in stat.columns:
                    raise util.CytoflowViewError('feature',
                                                 "Can't find feature '{}' in the statistic columns."
                                                 .format(self.feature))
            
                unused_stat_levels -= set([self.variable])
                
        if unused_locs_levels != unused_stat_levels:
            if self.style != "heat" and self.variable:
                raise util.CytoflowViewError('locations',
                                             f"After removing 'variable' {self.variable}, unused levels in 'statistic' are {unused_stat_levels}; unused levels in 'locations' are {unused_locs_levels}. They should be the same!")
            else:
                raise util.CytoflowViewError('locations',
                                             f"Unused levels in 'statistic' are {unused_stat_levels}; unused levels in 'locations' are {unused_locs_levels}. They should be the same!")

        if unused_stat_levels:
            stat_names = [x for x in stat.index.names if x in unused_stat_levels]
            stat_groupby = stat.groupby(stat_names, observed = True)
            return util.IterByWrapper(iter(stat_groupby.groups), stat_names)
        else:
            return util.IterByWrapper(iter([]), [])    
        
    def _get_stat(self, experiment):
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.statistic:
            raise util.CytoflowViewError('statistic', "Statistic not set")
        
        if self.statistic not in experiment.statistics:
            raise util.CytoflowViewError('statistic',
                                         "Can't find the statistic {} in the experiment"
                                         .format(self.statistic))
            
        stat = experiment.statistics[self.statistic]
                
        return stat
    
    def _get_locs(self, experiment):
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.locations:
            raise util.CytoflowViewError('location', "Location not set")
        
        if self.locations not in experiment.statistics:
            raise util.CytoflowViewError('location',
                                         "Can't find the location statistic {} in the experiment"
                                         .format(self.locations))
            
        locs = experiment.statistics[self.locations]

        return locs
    
    def _subset_data(self, stat_name, data):
        
        if self.subset:
            try:
                # TODO - either sanitize column names, or check to see that
                # all conditions are valid Python variables
                data = data.query(self.subset)
            except Exception as e:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{}' isn't valid for '{}'"
                                             .format(self.subset, stat_name)) from e
                
            if len(data) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{}' returned no values from '{}'"
                                             .format(self.subset, stat_name))
                
        names = list(data.index.names)
        
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                warn("Only one value for level {} in {}; dropping it.".format(name, stat_name),
                     util.CytoflowViewWarning)
                try:
                    data.index = data.index.droplevel(name)
                except AttributeError as e:
                    raise util.CytoflowViewError(None,
                                                 "Must have more than one "
                                                 "value to plot.") from e
                                                 
        # droplevel makes this a plain Index instead of a MultiIndex. no bueno.
        if not isinstance(data.index, pd.MultiIndex):
            data.index = pd.MultiIndex.from_tuples([(x,) for x in data.index.to_list()], 
                                                   names = [data.index.name])

        return data
        
    
# def pie(x, loc, **kwargs):

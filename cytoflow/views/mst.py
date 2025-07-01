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
cytoflow.views.matrix
---------------------
"""

import math
from warnings import warn

from traits.api import provides, Enum, Str, Callable, Constant, List
import seaborn as sns
from natsort import natsorted
import matplotlib as mpl
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import Grid, ImageGrid
from scipy.spatial.distance import cdist
import igraph
import numpy as np

import cytoflow
import cytoflow.utility as util

from .i_view import IView
from .base_views import BaseStatisticsView

@provides(IView)
class MSTView(BaseStatisticsView):
    """
    A view that creates a minimum spanning tree view of a statistic. 
    
    Set `statistic` to the name of the statistic to plot; set `feature` to the name
    of that statistic's feature you'd like to analyze. Then, set `location` to
    *another* statistic whose features are the locations (in any number of dimensions)
    of the nodes in the tree -- usually these are cluster centroids from `KMeansOp`
    or `SOMOp` (see the example below). The view computes a minimum-spanning tree 
    containing the nodes and lays it out in two dimensions.
    
    There are three different ways of plotting the value at each location in tree: 
    
    * Setting `style` to ``heat`` (the default) will produce a "traditional" heat map, 
      where each location is a circle and the color of the circle is related to the 
      intensity of the value of `feature`. (In this scenario, `variable` must be left empty.).
      
    * Setting `style` to ``pie`` will draw a pie plot at each location. The values of `variable`
      are used as the categories of the pie, and the arc length of each slice of pie is related 
      to the intensity of the value of `feature`.
      
    * Setting `style` to ``petal`` will draw a "petal plot" in each cell. The values of `variable` 
      are used as the categories, but unlike a pie plot, the arc width of each slice
      is equal. Instead, the radius of the pie slice scales with the square root of
      the intensity, so that the relationship between area and intensity remains the same.
      
..
    Optionally, you can set `size_feature` to scale the circles (or pies or petals)
    by another feature of the statistic. (Often used to scale by the count of a particular
    population or subset.)
    
    Attributes
    ----------
        
    statistic : Str
        The statistic to plot. Must be a key in `Experiment.statistics`.
        
    location : Str
        A statistic whose levels are the same as `statistic` and whose features
        are the dimensions of the locations of each node to plot.
        
    location_features : List(Str)
        Which features in `location` to use. By default, use all of them. 
        
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
        What kind of matrix plot to make?
        
    scale : {'linear', 'log', 'logicle'}
        How should the color, arc length, or radii be scaled before
        plotting?
        
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
        
..
    size_feature : String
        Which feature to use to scale the size of the circle/pie/petal?

..        
    size_function : String
        If `size_feature` is set and `style` is ``pie`` or ``petal``, this function
        is used to reduce `size_feature` before scaling the pie plots. The function 
        should take a `pandas.Series` and return a ``float``. Often something like
        ``lambda x: x.sum()``.
        
    Note
    ----
    `MSTView` is *not* a subclass of `BaseView` or any of its descendants.
    It implements the `IView` but does it does not use `seaborn.FacetGrid` 
    for laying out its plots.
    
    """
    
    id = Constant("cytoflow.view.matrix")
    friendly_id = Constant("Matrix Chart") 
    
    statistic = Str
    location = Str
    location_features = List(Str)
    variable = Str
    feature = Str
    scale = util.ScaleEnum
    style = Enum("heat", "pie", "petal")
    metric = Str("euclidean")
    
    size_feature = Str
    size_function = Callable

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
            
        All other parameters are passed to ???.

        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")

        if self.style == "heat" and self.variable != "":
            raise util.CytoflowViewError("variable",
                                         "If `style` is \"heat\", `variable` must be empty!")
                        
        stat = self._get_stat(experiment)
        locs = self._get_locs(experiment)
                
        stat = self._subset_data(stat)
        locs = self._subset_data(locs)
        
        locs_names = set(stat.index.names) - set([self.variable]) if self.variable else set(stat.index.names)
        if locs_names != set(locs.index.names):
            raise util.CytoflowViewError('location',
                                         "Levels of 'locations' are not the same as levels of 'statistic'")
            
        for lf in self.location_features:
            if lf not in locs:
                raise util.CytoflowViewError('location_features',
                                             "Feature {} not found in location statistic {}"
                                             .format(lf, self.location))
        
        unused_names = list(set(stat.index.names) - set([self.variable]))

        if plot_name is not None and not unused_names:
            raise util.CytoflowViewError('plot_name',
                                         "You specified a plot name, but all "
                                         "the facets are already used")

        if self.style != "heat" and self.variable not in stat.index.names:
            raise util.CytoflowViewError('variable',
                                         "Can't find variable '{}' in the statistic index."
                                         .format(self.variable))
        
        if self.size_feature and self.size_feature not in stat:
            raise util.CytoflowViewError('size_feature',
                                         "Feature {} not in statistic {}"
                                         .format(self.size_feature, self.statistic))

        title = kwargs.pop("title", None)
        legend = kwargs.pop('legend', True)
        legendlabel = kwargs.pop('legendlabel', self.feature)
                
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
        
        data = stat.reset_index()
        
        # set up the range of the color map
        if 'norm' not in kwargs:
            data_scale = util.scale_factory(scale = self.scale,
                                            experiment = experiment,
                                            statistic = self.statistic,
                                            features = [self.feature])
            data_norm = data_scale.norm()
        else:
            data_norm = kwargs.pop('norm')
            
            
        # groupby = data.groupby(locs_names, observed = True)
        
        # first, find the locations for the groups
        # MST logic: https://github.com/saeyslab/FlowSOM_Python/blob/d8cb6a5934b1ca9c82f4bba27a1f3cd9862a0596/src/flowsom/main.py#L255
        
        # compute the all-pairs distances
        locs_values = locs[self.location_features].values if self.location_features else locs.values
        adjacency_graph = cdist(locs_values, locs_values, self.metric)
        
        # create a fully-connected graph
        full_graph = igraph.Graph.Weighted_Adjacency(adjacency_graph, mode = "undirected", loops = False)
        
        # create the spanning tree
        mst_graph = igraph.Graph.spanning_tree(full_graph, weights = full_graph.es["weight"])
        
        # normalize the edge weights (necessary??)
        mst_graph.es["weight"] = mst_graph.es["weight"] / np.mean(mst_graph.es["weight"]) 
        
        # optimize the layout for plotting
        layout = mst_graph.layout_kamada_kawai(seed = mst_graph.layout_grid(),
                                               maxiter = 50 * mst_graph.vcount(),
                                               kkconst = max([mst_graph.vcount(), 1]))
        layout.fit_into((0.1, 0.1, 0.9, 0.9))

        # next, plot the edges connecting nodes
        segments = [[layout.coords[edge[0]], layout.coords[edge[1]]] for edge in mst_graph.get_edgelist()]
        segments = mpl.collections.LineCollection(segments, zorder = 1)
        segments.set_edgecolor("black")
        plt.gca().add_collection(segments)
        
        # now, plot the patches
                
        if self.style == "heat":
            cmap_name = kwargs.pop('palette', 'viridis')
            cmap = sns.color_palette(cmap_name, as_cmap = True)
            if isinstance(cmap, list):
                raise util.CytoflowViewError('palette',
                                             "{} is a qualitative (discrete) palette. Choose a continuous one such as 'rocket', 'mako' or 'viridis'")
                    
            patches = []
            for idx, x in enumerate(data[self.feature]):
                patch = mpl.patches.Circle(xy = layout.coords[idx], 
                                           radius = 0.1, 
                                           facecolor = cmap(data_norm(x)))
                patches.append(patch)
                
            plt.gca().add_collection(mpl.collections.PatchCollection(patches, match_original = True))
                
                
            if legend:
                plt.colorbar(mpl.cm.ScalarMappable(norm = data_norm, cmap = cmap),
                             ax = plt.gca(),
                             label = legendlabel)

        elif self.style == "pie":
            palette_name = kwargs.pop('palette', 'deep')
        
            # the context manager goes here because the color cycler is a
            # property of the axes 
            # with sns.color_palette(palette_name):
            #     grid = ImageGrid(fig = plt.gcf(), 
            #                      rect = 111, 
            #                      nrows_ncols = (len(rows) if len(rows) > 0 else 1, 
            #                                     len(cols) if len(cols) > 0 else 1),
            #                      label_mode = "keep",
            #                      axes_pad = 0.0,
            #                      cbar_mode = None)
            
            groups = data.groupby([self.variable], observed = True)
        
            for idx, (_, group) in enumerate(groups):
                group = group[self.feature]
                group = group / group.sum()
                print(group)
                # plt.sca(grid[idx])
                # patches, _ = plt.pie(group[self.feature], **kwargs)
                #
                # for pi, patch in enumerate(patches):
                #     patch.set_label(group.reset_index().at[pi, self.variable])
        
            # if(legend):
            #     grid.axes_row[0][-1].legend(bbox_to_anchor = (1, 1), 
            #                                 title = self.feature)
        #
        # elif self.style == "petal":
        #     palette_name = kwargs.pop('palette', 'deep')
        #
        #     # the context manager goes here because the color cycler is a
        #     # property of the axes 
        #     with sns.color_palette(palette_name):
        #         grid = ImageGrid(fig = plt.gcf(), 
        #                          rect = 111, 
        #                          nrows_ncols = (len(rows) if len(rows) > 0 else 1, 
        #                                         len(cols) if len(cols) > 0 else 1),
        #                          label_mode = "keep",
        #                          axes_pad = 0.0,
        #                          cbar_mode = None)
        #
        #     for idx, (_, group) in enumerate(groups):
        #         plt.sca(grid[idx])
        #         patches, _ = plt.pie([1.0 / len(group[self.feature])] * len(group[self.feature]), **kwargs)
        #
        #         for pi, patch in enumerate(patches):
        #             patch.set_label(group.reset_index().at[pi, self.variable])
        #             patch.set(radius = math.sqrt(group.reset_index().at[pi, self.feature] / group.reset_index()[self.feature].sum()))
        #
        #     if(legend):
        #         grid.axes_row[0][-1].legend(bbox_to_anchor = (1, 1), title = self.feature)
            

        # make axes equal (spacing)
        plt.gca().axis('equal')
        plt.gca().set_axis_off()
        
        if title:
            plt.suptitle(title, y = 1.02)
        
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
        
        if self.feature not in stat:
            raise util.CytoflowViewError('feature',
                                         "Can't find feature {} in statistic {}. "
                                         "Possible features: {}"
                                         .format(self.feature, self.statistic, stat.columns.to_list()))
                
        return stat
    
    def _get_locs(self, experiment):
        
        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")
        
        if not self.location:
            raise util.CytoflowViewError('location', "Location not set")
        
        if self.location not in experiment.statistics:
            raise util.CytoflowViewError('location',
                                         "Can't find the location statistic {} in the experiment"
                                         .format(self.location))
            
        locs = experiment.statistics[self.location]

        return locs
    
    def _subset_data(self, data):
        
        if self.subset:
            try:
                # TODO - either sanitize column names, or check to see that
                # all conditions are valid Python variables
                data = data.query(self.subset)
            except Exception as e:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' isn't valid"
                                             .format(self.subset)) from e
                
            if len(data) == 0:
                raise util.CytoflowViewError('subset',
                                             "Subset string '{0}' returned no values"
                                             .format(self.subset))
                
        names = list(data.index.names)
        
        for name in names:
            unique_values = data.index.get_level_values(name).unique()
            if len(unique_values) == 1:
                warn("Only one value for level {}; dropping it.".format(name),
                     util.CytoflowViewWarning)
                try:
                    data.index = data.index.droplevel(name)
                except AttributeError as e:
                    raise util.CytoflowViewError(None,
                                                 "Must have more than one "
                                                 "value to plot.") from e

        return data
        
    
# def pie(x, loc, **kwargs):

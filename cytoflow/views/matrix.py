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

from traits.api import provides, Enum, Str, Callable, Constant
import matplotlib.pyplot as plt

import cytoflow.utility as util

from .i_view import IView
from .base_views import BaseStatisticsView

@provides(IView)
class MatrixView(BaseStatisticsView):
    """
    A view that creates a matrix view (a 2D grid representation) of a statistic. 
    Set `statistic` to the name of the statistic to plot; set `feature` to the name
    of that statistic's feature you'd like to analyze.
    
    Setting `xfacet` and `yfacet` to levels of the statistic's index will result in
    a separate column or row for each value of that statistic.
    
    There are three different ways of plotting the values of the matrix view 
    (the "cells" in the matrix), controlled by the `type` parameter:
    
    * Setting `style` to ``heat`` (the default) will produce a "traditional" heat map, 
      where each "cell" is a circle and the color of the circle is related to the 
      intensity of the value of `feature`. (In this scenario, `variable` must be left empty.).
      
    * Setting `style` to ``pie`` will draw a pie plot in each cell. The values of `variable`
      are used as the categories of the pie, and the arc length of each slice of pie is related 
      to the intensity of the value of `feature`.
      
    * Setting `style` to ``petal`` will draw a "petal plot" in each cell. The values of `variable` 
      are used as the categories, but unlike a pie plot, the arc width of each slice
      is equal. Instead, the radius of the pie slice scales with the square root of
      the intensity, so that the relationship between area and intensity remains the same.
          
    Optionally, you can set `size_feature` to scale the circles' (or pies or petals)' area
    by another feature of the statistic. For example, you might scale the size of each
    circle by the number of events in some subset. For the ``heat`` style, this is 
    enough -- but for ``pie`` or ``petal`` plots, you need to *reduce* the feature
    (because there is only one pie plot, but there are multiple slices of the pie.)
    Set `size_function` to a callable that takes a `pandas.Series` as an argument and returns
    a ``float``.
    
    Attributes
    ----------
    
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
        
    size_feature : String
        Which feature to use to scale the size of the circle/pie/petal?
        
    size_function : String
        If `size_feature` is set and `style` is ``pie`` or ``petal``, this function
        is used to reduce `size_feature` before scaling the pie plots. The function 
        should take a `pandas.Series` and return a ``float``. Often something like
        ``lambda x: x.sum()``.


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
        
    Add a threshold gate
    
    .. plot::
        :context: close-figs
    
        >>> ex2 = flow.ThresholdOp(name = 'Threshold',
        ...                        channel = 'Y2-A',
        ...                        threshold = 2000).apply(ex)
        
    Add a statistic
    
    .. plot::
        :context: close-figs

        >>> ex3 = flow.ChannelStatisticOp(name = "ByDox",
        ...                               channel = "Y2-A",
        ...                               by = ['Dox', 'Threshold'],
        ...                               function = len).apply(ex2) 
    
    Plot the bar chart
    
    .. plot::
        :context: close-figs
        
        >>> flow.MatrixView(statistic = "ByDox",
        ...                 xfacet = 'Dox',
        ...                 variable = 'Threshold',
        ...                 feature = 'Y2-A',
        ...                 style = 'pie').plot(ex3)
        
    """
    
    id = Constant("cytoflow.view.matrix")
    friendly_id = Constant("Matrix Chart") 
    
    variable = Str
    feature = Str
    scale = util.ScaleEnum
    style = Enum("heat", "pie", "petal")
    huefacet = Constant("")   # can't facet by hue
    huescale = Constant("linear")   # can't facet by hue. use `scale`.
    
    size_feature = Str
    size_function = Callable

    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot a chart of a variable's values against a statistic.
        
        Parameters
        ----------

        """
        
        if self.huefacet:
            raise util.CytoflowViewError('huefacet',
                                         "Cannot set huefacet with this view.")
        
        if self.style == "heat" and self.variable != "":
            raise util.CytoflowViewError("variable",
                                         "If `style` is \"heat\", `variable` must be empty!")
            
            
        stat = self._get_stat(experiment)
        
        if self.style != "heat" and self.variable not in stat.index.names:
            raise util.CytoflowViewError('variable',
                                         "Can't find variable '{}' in the statistic index."
                                         .format(self.variable))
        
        if self.size_feature and self.size_feature not in stat:
            raise util.CytoflowViewError('size_feature',
                                         "Feature {} not in statistic {}"
                                         .format(self.size_feature, self.statistic))
            
        kwargs.setdefault('aspect', 1.0)
        kwargs.setdefault('margin_titles', True)
        
        # xlabel and ylabel are the axis labels for the facet axes. of course,
        # we don't have any -- so clear them out.
        kwargs.setdefault('xlabel', " ") 
        kwargs.setdefault('ylabel', " ")
        
        # put the legend outside of the grid.
        kwargs.setdefault('legend_out', True)
        
        super().plot(experiment, plot_name, **kwargs)

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
    
    def _get_facets(self, data):
        if self.variable:            
            if self.variable not in data.index.names:
                raise util.CytoflowViewError('variable',
                                             "Variable {} not found in the data. Must be one of {}"
                                             .format(self.variable, data.index.names))
                
            facets = super()._get_facets(data) + [self.variable]
        else:
            facets = super()._get_facets(data)
                    
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError(None, "Can't reuse facets")
        
        return facets
    

    def _grid_plot(self, experiment, grid, **kwargs):

        if self.size_feature and self.size_function:
            for _, group in grid.facet_data():
                try:
                    v = self.size_function(group[self.size_feature])
                except Exception as e:
                    raise util.CytoflowViewError(None,
                                               "Your function threw an error in group {}"
                                               .format(group)) from e
                                               
                try:
                    v = float(v)
                except (TypeError, ValueError) as e:
                    raise util.CytoflowOpError(None,
                                               "Your function returned a {}. It must return "
                                               "a float or a value that can be cast to float."
                                               .format(type(v))) from e
                                               
                grid.data.loc[group.index, '_scale'] = v
        elif self.size_feature:
            grid.data['_scale'] = grid.data[self.size_feature]
        else:
            grid.data['_scale'] = [1.0] * len(grid.data)
            
        grid.data['_scale'] = grid.data['_scale'] / grid.data['_scale'].max()
                    
        if self.style == "heat":
            # set the default color map
            kwargs.setdefault('cmap', plt.get_cmap('viridis'))
            
            # set up the range of the color map
            if 'norm' not in kwargs:
                hue_scale = util.scale_factory(scale = self.scale,
                                               experiment = experiment,
                                               statistic = self.statistic,
                                               features = [self.feature])
                
                kwargs['norm'] = hue_scale.norm()
                
            grid.map(_heat_plot, self.feature, '_scale', **kwargs)
            
            return {"cmap" : kwargs['cmap'], 
                    "norm" : kwargs['norm']}
            
        elif self.style == "pie":
            patches = {}
            
            arc_scale = util.scale_factory(scale = self.scale,
                                           experiment = experiment,
                                           statistic = self.statistic,
                                           features = [self.feature])
            
            kwargs['norm'] = arc_scale.norm()
            
            grid.map(_pie_plot, self.feature, "_scale", patches = patches, **kwargs)
            
            # legends only get added in BaseView.plot for hue facets, so we need to add one here.
            grid.add_legend(title = self.variable, 
                            legend_data = dict(zip(grid.data[self.variable].unique(),
                                                   [plt.Rectangle((0, 0), 1, 1, fc = p.get_facecolor()) for p in patches[plt.gca()]])),
                            loc = 1)
        
            return {}
    
        elif self.style == "petal":
            patches = {}
            rad_scale = util.scale_factory(scale = self.scale,
                                           experiment = experiment,
                                           statistic = self.statistic,
                                           features = [self.feature])
            
            kwargs['norm'] = rad_scale.norm()
            grid.map(_petal_plot, self.feature, "_scale", patches = patches, **kwargs)
            
            # legends only get added in BaseView.plot for hue facets, so we need to add one here.
            grid.add_legend(title = self.variable, 
                            legend_data = dict(zip(grid.data[self.variable].unique(),
                                                   [plt.Rectangle((0, 0), 1, 1, fc = p.get_facecolor()) for p in patches[plt.gca()]])),
                            loc = 1)
        
            return {}

util.expand_class_attributes(MatrixView)
util.expand_method_parameters(MatrixView, MatrixView.plot)

def _heat_plot(data, size, color = None, **kws):
    cmap = kws.pop('cmap')
    norm = kws.pop('norm')
    
    pie_patches, _ = plt.pie(data, **kws)
    
    pie_patches[0].set_facecolor(cmap(norm(data.iat[0])))
    pie_patches[0].set(radius = size.iat[0])            

    
def _pie_plot(data, size, patches, color = None, **kws):
    norm = kws.pop('norm')
    pie_patches, _ = plt.pie(data, **kws)
    for patch in pie_patches:
        patch.set(radius = norm(size.iat[0]))

    patches[plt.gca()] = pie_patches
    

def _petal_plot(data, patches, color = None, **kws):  
    
    norm = kws.pop('norm')
    pie_patches, _ = plt.pie([1.0 / len(data)] * len(data), **kws)
    for i, p in enumerate(pie_patches):
        p.set(radius = math.sqrt(p.r * norm(data.iat[i])))
        
    patches[plt.gca()] = pie_patches        

    

        
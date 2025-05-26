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

from traits.api import provides, Enum, Str
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
      
    * Set `style` to ``petal`` will draw a "petal plot" in each cell. The values of `variable` 
      are used as the categories, but unlike a pie plot, the arc width of each slice
      is equal. Instead, the radius of the pie slice scales with the square root of
      the intensity, so that the relationship between area and intensity remains the same.
          
    Optionally, you can set `size_feature` to scale the circles' (or pies or petals)' area
    by another feature of the statistic. (Often used to scale by the count of a particular
    population or subset.)
    
    Attributes
    ----------
    
    variable : Str
        The variable used for plotting pie and petal plots. Must be left empty
        for a heatmap.
        
    feature : Str
        The column in the statistic to plot (often a channel name.)
        
    style : Enum(``heat``, ``pie``, ``petal``) (default = ``heat``)
        What kind of matrix plot to make?
    """
    
    variable = Str
    feature = Str
    scale = util.ScaleEnum
    style = Enum("heat", "pie", "petal")

    def plot(self, experiment, plot_name = None, **kwargs):
        """
        Plot a chart of a variable's values against a statistic.
        
        Parameters
        ----------
        
        soem parameters...
        """
        
        if self.huefacet:
            raise util.CytoflowViewError('huefacet',
                                         "Cannot set huefacet with this view.")
        
        if self.style == "heat" and self.variable != "":
            raise util.CytoflowViewError("variable",
                                         "If`type` is \"heat\", `variable` must be empty!")
            
        kwargs.setdefault('aspect', 1.0)
        kwargs.setdefault('margin_titles', True)
        kwargs.setdefault('xlabel', " ")  # I'm not sure why self.feature gets used as the x axis label otherwise.
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
                
            grid.map(_heat_plot, self.feature, **kwargs)
            
            return {"cmap" : kwargs['cmap'], 
                    "norm" : kwargs['norm']}
            
        elif self.style == "pie":
            patches = {}
            grid.map(_pie_plot, self.feature, patches = patches, **kwargs)
            
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
            grid.map(_petal_plot, self.feature, patches = patches, **kwargs)
            
            # legends only get added in BaseView.plot for hue facets, so we need to add one here.
            grid.add_legend(title = self.variable, 
                            legend_data = dict(zip(grid.data[self.variable].unique(),
                                                   [plt.Rectangle((0, 0), 1, 1, fc = p.get_facecolor()) for p in patches[plt.gca()]])),
                            loc = 1)
        
            return {}


def _heat_plot(data, color = None, **kws):
    cmap = kws.pop('cmap')
    norm = kws.pop('norm')
    pie_patches, _ = plt.pie(data, **kws)
    
    pie_patches[0].set_facecolor(cmap(norm(data.iat[0])))            

    
def _pie_plot(data, patches, color = None, **kws):
    pie_patches, _ = plt.pie(data, **kws)
    patches[plt.gca()] = pie_patches

def _petal_plot(data, patches, color = None, **kws):  
    
    norm = kws.pop('norm')
    pie_patches, _ = plt.pie([1.0 / len(data)] * len(data), **kws)
    for i, p in enumerate(pie_patches):
        p.set(radius = math.sqrt(p.r * norm(data.iat[i])))
        
    patches[plt.gca()] = pie_patches        

        

        
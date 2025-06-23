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
cytoflow.views.violin
---------------------

A violin plot is a facetted set of kernel density estimates.

`ViolinPlotView` -- the `IView` class that makes the plot.
"""

import warnings

from traits.api import Str, provides, Constant

import numpy as np
import matplotlib.pyplot as plt
from seaborn import violinplot

import cytoflow.utility as util
from .i_view import IView
from .base_views import Base1DView

@provides(IView)
class ViolinPlotView(Base1DView):
    """
    Plots a violin plot -- a facetted set of kernel density estimates.
    
    Attributes
    ----------

    variable : Str
        the main variable by which we're faceting
    
        
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
        
    Plot a violin plot
    
    .. plot::
        :context: close-figs
    
        >>> flow.ViolinPlotView(channel = 'Y2-A',
        ...                     scale = 'log',
        ...                     variable = 'Dox').plot(ex)
    """
    
    # traits   
    id = Constant("cytoflow.view.violin")
    friendly_id = Constant("Violin Plot")

    variable = Str
    
    def plot(self, experiment, **kwargs):
        """
        Plot a violin plot of a variable
        
        Parameters
        ----------
        
        bw : {{'scott', 'silverman', float}}, optional
            Either the name of a reference rule or the scale factor to use when
            computing the kernel bandwidth. The actual kernel size will be
            determined by multiplying the scale factor by the standard deviation of
            the data within each bin.

        scale_plot : {{"area", "count", "width"}}, optional
            The method used to scale the width of each violin. If ``area``, each
            violin will have the same area. If ``count``, the width of the violins
            will be scaled by the number of observations in that bin. If ``width``,
            each violin will have the same width.
            
        scale_hue : bool, optional
            When nesting violins using a ``hue`` variable, this parameter
            determines whether the scaling is computed within each level of the
            major grouping variable (``scale_hue=True``) or across all the violins
            on the plot (``scale_hue=False``).
            
        gridsize : int, optional
            Number of points in the discrete grid used to compute the kernel
            density estimate.

        inner : {{"box", "quartile", None}}, optional
            Representation of the datapoints in the violin interior. If ``box``,
            draw a miniature boxplot. If ``quartiles``, draw the quartiles of the
            distribution.  If ``point`` or ``stick``, show each underlying
            datapoint. Using ``None`` will draw unadorned violins.
            
        split : bool, optional
            When using hue nesting with a variable that takes two levels, setting
            ``split`` to True will draw half of a violin for each level. This can
            make it easier to directly compare the distributions.

        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
        
        if not self.variable:
            raise util.CytoflowViewError('variable',
                                         "Variable not specified")
        
        facets = [x for x in [self.xfacet, self.yfacet, self.huefacet, self.variable] if x]
        if len(facets) != len(set(facets)):
            raise util.CytoflowViewError("Can't reuse facets")
        
        # for some reason, seaborn's violinplot REALLY dislikes very small values on a log scale
        # make a tiny little experiment with just the plot channel and conditions, then drop
        # any bad events.
        if self.channel and self.scale == "log" and (experiment.data[self.channel] < 0.001).any():
            warnings.warn("Dropping small values in channel {}".format(self.channel),
                          util.CytoflowViewWarning)
            experiment = experiment.clone(deep = False)
            experiment.data = experiment.data[ list(experiment.conditions.keys()) + [self.channel]]
            experiment.data = experiment.data.loc[experiment.data[self.channel] > 0.001]
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, cmap, **kwargs):

        kwargs.setdefault('orientation', 'vertical')
        
        scale = kwargs.pop('scale')[self.channel]
        lim = kwargs.pop('lim')[self.channel]
                
        # set the scale for each set of axes; can't just call plt.xscale() 
        for ax in grid.axes.flatten():
            if kwargs['orientation'] == 'horizontal':
                ax.set_xscale(scale.name, **scale.get_mpl_params(ax.get_xaxis()))  
            else:
                ax.set_yscale(scale.name, **scale.get_mpl_params(ax.get_yaxis()))  
            
        # if kwargs['orientation'] == 'horizontal':
        #     violin_args = [self.channel, self.variable]
        # else:
        #     violin_args = [self.variable, self.channel]
        
        if kwargs['orientation'] == 'horizontal':
            kwargs['x'] = self.channel
            kwargs['y'] = self.variable
            kwargs['orient'] = 'h'
        else:
            kwargs['x'] = self.variable
            kwargs['y'] = self.channel
            kwargs['orient'] = 'v'
            
        # sns.violinplot expects "orient", not "orientation"
        del kwargs['orientation']
                        
        # the bw kwarg was deprecated in seaborn 0.13, but the meaning of bw_method
        # is the same. there's also a scaling factor, bw_adjust, which can be 
        # used but I haven't documented.
        if 'bw' in kwargs:
            kwargs['bw_method'] = kwargs['bw']
            del kwargs['bw']
            
        # the scale_plot kwarg was deprecated in seaborn 0.13, but density_norm
        # is a direct replacement.
        if 'scale_plot' in kwargs:
            kwargs['density_norm'] = kwargs['scale_plot']
            del kwargs['scale_plot']
            
        # the scale_hue kwarg was deprecated in seaborn 0.13, but common_norm 
        # is a direct replacement
        if 'scale_hue' in kwargs:
            kwargs['common_norm'] = kwargs['scale_hue']
            del kwargs['scale_hue']
            
        grid.map_dataframe(violinplot,       
                           order = np.sort(experiment[self.variable].unique()),
                           hue_order = (np.sort(experiment[self.huefacet].unique()) if self.huefacet else None),
                           **kwargs)
        
        if kwargs['orient'] == 'h':
            return {"xscale" : scale, "xlim" : lim}
        else:
            return {"yscale" : scale, "ylim" : lim}
        

util.expand_class_attributes(ViolinPlotView)
util.expand_method_parameters(ViolinPlotView, ViolinPlotView.plot)
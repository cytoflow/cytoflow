#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
cytoflow.views.violin
---------------------
'''

from traits.api import Str, provides, Constant

import numpy as np
import matplotlib.pyplot as plt

import cytoflow.utility as util
from .i_view import IView
from .base_views import Base1DView

@provides(IView)
class ViolinPlotView(Base1DView):
    """Plots a violin plot -- a facetted set of kernel density estimates.
    
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
    id = Constant("edu.mit.synbio.cytoflow.view.violin")
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
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, **kwargs):

        kwargs.setdefault('orientation', 'vertical')
        
        scale = kwargs.pop('scale')[self.channel]
        lim = kwargs.pop('lim')[self.channel]
                
        # set the scale for each set of axes; can't just call plt.xscale() 
        for ax in grid.axes.flatten():
            if kwargs['orientation'] == 'horizontal':
                ax.set_xscale(scale.name, **scale.get_mpl_params(ax.get_xaxis()))  
            else:
                ax.set_yscale(scale.name, **scale.get_mpl_params(ax.get_yaxis()))  
            
        # this order-dependent thing weirds me out.      
        if kwargs['orientation'] == 'horizontal':
            violin_args = [self.channel, self.variable]
        else:
            violin_args = [self.variable, self.channel]
            
        if self.huefacet:
            violin_args.append(self.huefacet)
            
        grid.map(_violinplot,   
                 *violin_args,      
                 order = np.sort(experiment[self.variable].unique()),
                 hue_order = (np.sort(experiment[self.huefacet].unique()) if self.huefacet else None),
                 data_scale = scale,
                 **kwargs)
        
        if kwargs['orientation'] == 'horizontal':
            return {"xscale" : scale, "xlim" : lim}
        else:
            return {"yscale" : scale, "ylim" : lim}
        
# this uses an internal interface to seaborn's violin plot.

from seaborn.categorical import _ViolinPlotter

def _violinplot(x=None, y=None, hue=None, data=None, order=None, hue_order=None,
                bw="scott", cut=2, scale_plot="area", scale_hue=True, gridsize=100,
                width=.8, inner="box", split=False, dodge=True, orientation=None, linewidth=None,
                color=None, palette=None, saturation=.75, ax=None, data_scale = None,
                **kwargs):
    
    # discards kwargs
    
    if orientation and orientation == 'horizontal':
        x = data_scale(x)
    else:
        y = data_scale(y)
            
    plotter = _ViolinPlotter(x, y, hue, data, order, hue_order,
                             bw, cut, scale_plot, scale_hue, gridsize,
                             width, inner, split, dodge, orientation, linewidth,
                             color, palette, saturation)

    for i in range(len(plotter.support)):
        if plotter.hue_names is None:       
            if plotter.support[i].shape[0] > 0:
                plotter.support[i] = data_scale.inverse(plotter.support[i])
        else:
            for j in range(len(plotter.support[i])):
                if plotter.support[i][j].shape[0] > 0:
                    plotter.support[i][j] = data_scale.inverse(plotter.support[i][j])

    for i in range(len(plotter.plot_data)):
        plotter.plot_data[i] = data_scale.inverse(plotter.plot_data[i])

    if ax is None:
        ax = plt.gca()

    plotter.plot(ax)
    return ax


util.expand_class_attributes(ViolinPlotView)
util.expand_method_parameters(ViolinPlotView, ViolinPlotView.plot)
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
cytoflow.views.radviz
---------------------

A "Radviz" plot projects multivariate plots into two dimensions.

`RadvizView` -- the `IView` class that makes the plot.
"""

from traits.api import provides, Constant

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import scipy.spatial.distance

import pandas as pd
import numpy as np

import cytoflow.utility as util
from .i_view import IView

from .base_views import BaseNDView

@provides(IView)
class RadvizView(BaseNDView):
    """
    Plots a Radviz plot.  Radviz plots project multivariate plots into 
    two dimensions.  Good for looking for clusters.

    Attributes
    ----------
    
    Notes
    -----
    
    The Radviz plot is based on a method of "dimensional anchors" [#f1]_.
    The variables are conceived as points equidistant around a unit circle,
    and each data point connected to each anchor by a spring whose stiffness
    corresponds to the value of that data point.  The location of the data
    point is the location where springs' tensions are minimized.  Fortunately,
    there is fast matrix math to do this.
    
    As per [#f2]_, the order of the anchors can make a huge difference.  I've 
    adapted the code from the R ``radviz`` package [#f3]_ to compute the cosine
    similarity of all possible circular permutations ("necklaces").  For a
    moderate number of anchors such as is likely to be encountered here,
    computing them all is completely feasible.
    
    References
    ----------
        
    .. [#f1] Hoffman P, Grinstein G, Pinkney D. Dimensional anchors: a graphic 
        primitive for multidimensional multivariate information visualizations. 
        Proceedings of the 1999 workshop on new paradigms in information 
        visualization and manipulation in conjunction with the eighth ACM 
        internation conference on Information and knowledge management. 
        1999 Nov 1 (pp. 9-16). ACM.
    
    .. [#f2] Di Caro L, Frias-Martinez V, Frias-Martinez E. Analyzing the role 
        of dimension arrangement for data visualization in radviz. Advances in 
        Knowledge Discovery and Data Mining. 2010:125-32.
        
    .. [#f3] https://github.com/yannabraham/Radviz
        
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
        
    Plot the radviz.
    
    .. plot::
        :context: close-figs
    
        >>> flow.RadvizView(channels = ['B1-A', 'V2-A', 'Y2-A'],
        ...                 scale = {'Y2-A' : 'log',
        ...                          'V2-A' : 'log',
        ...                          'B1-A' : 'log'},
        ...                 huefacet = 'Dox').plot(ex)
            
    """
    
    id = Constant('edu.mit.synbio.cytoflow.view.radviz')
    friend_id = Constant("Radviz Plot")
        
    def plot(self, experiment, **kwargs):
        """
        Plot a faceted Radviz plot
        
        Parameters
        ----------
        
        alpha : float (default = 0.25)
            The alpha blending value, between 0 (transparent) and 1 (opaque).
            
        s : int (default = 2)
            The size in points^2.
            
        marker : a matplotlib marker style, usually a string
            Specfies the glyph to draw for each point on the scatterplot.
            See `matplotlib.markers <http://matplotlib.org/api/markers_api.html#module-matplotlib.markers>`_ for examples.  Default: 'o'
                    
        Notes
        -----
        Other ``kwargs`` are passed to `matplotlib.pyplot.scatter <https://matplotlib.org/devdocs/api/_as_gen/matplotlib.pyplot.scatter.html>`_
  
        """
        
        
        if len(self.channels) < 3:
            raise util.CytoflowViewError('channels',
                                         "Must have at least 3 channels")
        
        super().plot(experiment, **kwargs)
        
    def _grid_plot(self, experiment, grid, **kwargs):
        
        # xlim and ylim, xscale and yscale are the limits and scale of the
        # plane onto which we are projecting.  the kwargs 'scale' and 'lim'
        # are the data scale and limits, respectively
        
        scale = kwargs.pop('scale')
        lim = kwargs.pop('lim')
        
        # optimize anchor order
        df = pd.DataFrame()
        for c in self.channels:
            vmin = lim[c][0]
            vmax = lim[c][1]

            c_scaled = pd.Series(data = scale[c].norm(vmin = vmin, vmax = vmax)(grid.data[c].values),
                                 index = grid.data[c].index,
                                 name = c)
    
            c_scaled[(grid.data[c] < vmin) | (grid.data[c] > vmax)] = np.nan
            df[c] = c_scaled
            
        df.dropna(axis = 0, how = 'any', inplace = True)
        
        m = len(df.columns)
        s = np.array([(np.cos(t), np.sin(t))
                      for t in [2.0 * np.pi * (i / float(m))
                                for i in range(m)]])
        
        dotmat = np.dot(df.T.values, df.values)
        sim = dotmat / np.matmul(np.sqrt(np.diag(dotmat))[:, np.newaxis],
                                 np.sqrt(np.diag(dotmat))[np.newaxis, :])
                
        def similarity_metric(loc, sim, p):
            p_loc = loc[p]
            p_sim = sim[p]
            dist_array = scipy.spatial.distance.pdist(p_loc)
            dist_matrix = scipy.spatial.distance.squareform(dist_array)
            return -1.0 * np.sum(dist_matrix * p_sim)
        
        # for a modest number of anchors, just look permutations
        # no need for anything fancier.
        
        best_p = None
        best_score = -np.inf
        
        for p in _get_necklaces(np.arange(m)):
            score = similarity_metric(s, sim, p)

            if score > best_score:
                best_p = p
                best_score = score
                
        kwargs.setdefault('alpha', 0.25)
        kwargs.setdefault('s', 2)
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)
        
        # memo to track if we've put annotations on an axes yet
        ax_annotations = {}
                
        grid.map(_radviz_plot, 
                 *self.channels, 
                 ax_annotations = ax_annotations, 
                 scale = scale,
                 lim = lim,
                 order = best_p,
                 **kwargs)
   
        return {}
    
    def _update_legend(self, legend):
        for lh in legend.legend_handles:
            lh.set_alpha(0.5)
            lh.set_sizes([10.0])
            
    
def _radviz_plot(*channels, ax_annotations, scale, lim, order, **kwargs):

    color = kwargs.pop('color')
    
    df = pd.DataFrame()
    for c in channels:
        vmin = lim[c.name][0]
        vmax = lim[c.name][1]
        c_scaled = pd.Series(data = scale[c.name].norm(vmin = vmin, vmax = vmax)(c.values),
                             index = c.index,
                             name = c.name)

        c_scaled[(c < vmin) | (c > vmax)] = np.nan
        df[c.name] = c_scaled
        
    df.dropna(axis = 0, how = 'any', inplace = True)
    
    # reorder anchors
    df = df[df.columns[order]]
    
    # adapted from pandas.plotting._misc
    
    m = len(df.columns)
    s = np.array([(np.cos(t), np.sin(t))
                  for t in [2.0 * np.pi * (i / float(m))
                            for i in range(m)]])

    to_plot = [[], []]    
    for i in range(len(df)):
        row = df.iloc[i].values
        row_ = np.repeat(np.expand_dims(row, axis = 1), 2, axis = 1)
        y = (s * row_).sum(axis = 0) / row.sum()
        to_plot[0].append(y[0])
        to_plot[1].append(y[1])
    
    ax = plt.gca()
    
    ax.scatter(to_plot[0], to_plot[1], color = color, **kwargs)
    
    # have we already annotated these axes?
    if ax in ax_annotations:
        return
    
    ax_annotations[ax] = True
    
    ax.set_axis_off()
    for xy, name in zip(s, df.columns):

        ax.add_patch(patches.Circle(xy, radius=0.025, facecolor='gray'))

        if xy[0] < 0.0 and xy[1] < 0.0:
            ax.text(xy[0] - 0.025, xy[1] - 0.025, name,
                    ha='right', va='top', size='small')
        elif xy[0] < 0.0 and xy[1] >= 0.0:
            ax.text(xy[0] - 0.025, xy[1] + 0.025, name,
                    ha='right', va='bottom', size='small')
        elif xy[0] >= 0.0 and xy[1] < 0.0:
            ax.text(xy[0] + 0.025, xy[1] - 0.025, name,
                    ha='left', va='top', size='small')
        elif xy[0] >= 0.0 and xy[1] >= 0.0:
            ax.text(xy[0] + 0.025, xy[1] + 0.025, name,
                    ha='left', va='bottom', size='small')

    ax.axis('scaled')
    
def _get_necklaces(L):
    import itertools as it

    B = it.combinations(L,2)
    swaplist = [e for e in B]

    unique_necklaces = []
    unique_necklaces.append(L)
    for pair in swaplist:
        necklace = list(L)
        e1 = pair[0]
        e2 = pair[1]
        indexe1 = np.where(L == e1)[0][0]
        indexe2 = np.where(L == e2)[0][0]
        #swap
        necklace[indexe1],necklace[indexe2] = necklace[indexe2], necklace[indexe1]
        unique_necklaces.append(necklace)
    
    return unique_necklaces
    
util.expand_class_attributes(RadvizView)
util.expand_method_parameters(RadvizView, RadvizView.plot)

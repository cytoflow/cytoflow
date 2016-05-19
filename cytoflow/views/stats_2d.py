#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

from __future__ import division, absolute_import

from traits.api import HasStrictTraits, Str, provides, Callable
import matplotlib as mpl
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import pandas as pd

from .i_view import IView
import cytoflow.utility as util

@provides(IView)
class Stats2DView(HasStrictTraits):
    """
    Divide the data up by `by`, then plot a scatter plot of a summary
    statistic `xfunction` on the x axis vs a summary statistic `yfunction` of
    the same data on the y axis.
    
    Attributes
    ----------
    name : Str
        The plot's name 
    
    by : Str
        the name of the conditioning variable
        
    xchannel : Str
        Apply `xfunction` to `xchannel` for each value of `by`.
        
    xscale : Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the X axis
        
    xfunction : Callable
        What summary function to apply to `xchannel`
    
    ychannel : Str
        Apply `yfunction` to `ychannel` for each value of `by`
        
    yscale : Enum("linear", "log", "logicle") (default = "linear")
        What scale to use on the Y axis
        
    yfunction : Callable
        What summary function to apply to `ychannel`
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        
    yfacet : Str
        the conditioning variable for vertical subplots
        
    huefacet : 
        the conditioning variable for color.
        
    x_error_bars, y_error_bars : Enum(None, "data", "summary")
        draw error bars?  if `data`, apply `{x,y}_error_function` to the same
        data that was summarized with `function`.  if "summary", apply
        `{x,y}_error_function` to subsets defined by `{x,y}_error_var` 
        TODO - unimplemented
        
    x_error_var, y_error_var : Str
        the conditioning variable used to determine summary subsets.  take the
        data that was used to draw the bar; subdivide it further by 
        {x,y}_error_var; compute the summary statistic for each subset, then 
        apply {x,y}_error_function to the resulting list.
        TODO - unimplemented
        
    x_error_function, y_error_function : Callable (1D numpy.ndarray --> float)
        for each group/subgroup subset, call this function to compute the 
        error bars.  whether it is called on the data or the summary function
        is determined by the value of `{x,y}_error_bars`
        TODO - unimplemented
        
    subset : Str
        a string passed to Experiment.query() to subset the data before 
        we plot it.
        
    Examples
    --------
    
    Assume we want an input-output curve for a repressor that's under the
    control of a Dox-inducible promoter.  We have an "input" channel
    `(Dox --> eYFP, FITC-A channel)` and an output channel 
    `(Dox --> repressor --| eBFP, Pacific Blue channel)` as well as a 
    constitutive expression channel (mKate, PE-Tx-Red-YG-A channel). 
    We have induced several wells with different amounts of Dox.  We want 
    to plot the relationship between the input and output channels (binned by 
    input channel intensity) as we vary Dox, faceted by constitutive channel 
    bin.
    
    >>> ex_cfp_binned = flow.BinningOp(name = "CFP_Bin",
    ...                                channel = "PE-Tx-Red-YG-A",
    ...                                scale = "log",
    ...                                bin_width = 0.1).apply(ex)
    >>> ex_ifp_binned = flow.BinningOp(name = "IFP_Bin",
    ...                                channel = "Pacific Blue-A",
    ...                                scale = "log",
    ...                                bin_width = 0.1).apply(ex_cfp_binned)
    >>> view = flow.Stats2DView(name = "IFP vs OFP",
    ...                         by = "IFP_Bin",
    ...                         xchannel = "Pacific Blue-A",
    ...                         xfunction = flow.geom_mean,
    ...                         ychannel = "FITC-A",
    ...                         yfunction = flow.geom_mean,
    ...                         huefacet = "CFP_Bin").plot(ex_ifp_binned)
    >>> view.plot(ex_binned)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.stats2d"
    friendly_id = "2D Statistics View" 
    
    name = Str
    by = Str
    xchannel = Str
    xscale = util.ScaleEnum
    xfunction = Callable
    ychannel = Str
    yscale = util.ScaleEnum
    yfunction = Callable
    xfacet = Str
    yfacet = Str
    huefacet = Str
#     x_error_bars = Enum(None, "data", "summary")
#     x_error_function = Callable
#     x_error_var = Str
#     y_error_bars = Enum(None, "data", "summary")
#     y_error_function = Callable
#     y_error_var = Str
    subset = Str

    
    def plot(self, experiment, **kwargs):
        """Plot a bar chart"""
        
        if not experiment:
            raise util.CytoflowViewError("No experiment specified")
        
        if not self.by:
            raise util.CytoflowViewError("Independent variable 'by' not set")
            
        if self.by not in experiment.conditions:
            raise util.CytoflowViewError("Independent variable {0} not in the experiment"
                                    .format(self.by))
        
        if not (experiment.conditions[self.by] == "float" or
                experiment.conditions[self.by] == "int"):
            raise util.CytoflowViewError("by variable {0} isn't numeric"
                                    .format(self.by)) 
            
        if not self.xchannel:
            raise util.CytoflowViewError("X channel isn't set.")
        
        if self.xchannel not in experiment.data:
            raise util.CytoflowViewError("X channel {0} isn't in the experiment"
                                    .format(self.xchannel))
        
        if not self.xfunction:
            raise util.CytoflowViewError("X summary function isn't set")
                
        if not self.ychannel:
            raise util.CytoflowViewError("Y channel isn't set.")
        
        if self.ychannel not in experiment.data:
            raise util.CytoflowViewError("Y channel {0} isn't in the experiment"
                                    .format(self.ychannel))
        
        if not self.yfunction:
            raise util.CytoflowViewError("Y summary function isn't set")
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise util.CytoflowViewError("X facet {0} not in the experiment")
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise util.CytoflowViewError("Y facet {0} not in the experiment")
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise util.CytoflowViewError("Hue facet {0} not in the experiment")        

        kwargs.setdefault('antialiased', True)
        
        if self.subset:
            try:
                data = experiment.query(self.subset).data.reset_index()
            except:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(data.index) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
        else:
            data = experiment.data
            
        group_vars = [self.by]
        if self.xfacet: group_vars.append(self.xfacet)
        if self.yfacet: group_vars.append(self.yfacet)
        if self.huefacet: group_vars.append(self.huefacet)
            
        g = data.groupby(by = group_vars)
        
        plot_data = pd.DataFrame(
                {self.xchannel : g[self.xchannel].aggregate(self.xfunction), 
                 self.ychannel : g[self.ychannel].aggregate(self.yfunction)}) \
                      .reset_index()
 
        grid = sns.FacetGrid(plot_data,
                             size = 6,
                             aspect = 1.5,
                             col = (self.xfacet if self.xfacet else None),
                             row = (self.yfacet if self.yfacet else None),
                             hue = (self.huefacet if self.huefacet else None),
                             col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                             row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                             hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                             legend_out = False,
                             sharex = False,
                             sharey = False)
        
        xscale = util.scale_factory(self.xscale, experiment, self.xchannel)
        yscale = util.scale_factory(self.yscale, experiment, self.ychannel)
        
        for ax in grid.axes.flatten():
            ax.set_xscale(self.xscale, **xscale.mpl_params)
            ax.set_yscale(self.yscale, **yscale.mpl_params)

        grid.map(plt.plot, self.xchannel, self.ychannel, **kwargs)

        # if we have a hue facet and a lot of hues, make a color bar instead
        # of a super-long legend.
        
        if self.huefacet:
            current_palette = mpl.rcParams['axes.color_cycle']
            if len(grid.hue_names) > len(current_palette):
                plot_ax = plt.gca()
                cmap = mpl.colors.ListedColormap(sns.color_palette("husl", 
                                                                   n_colors = len(grid.hue_names)))
                cax, _ = mpl.colorbar.make_axes(plt.gca())
                norm = mpl.colors.Normalize(vmin = np.min(grid.hue_names), 
                                            vmax = np.max(grid.hue_names), 
                                            clip = False)
                mpl.colorbar.ColorbarBase(cax, cmap = cmap, norm = norm)
                plt.sca(plot_ax)
            else:
                grid.add_legend()

    
if __name__ == '__main__':
    import cytoflow as flow
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    thresh = flow.ThresholdOp()
    thresh.name = "Y2-A+"
    thresh.channel = 'Y2-A'
    thresh.threshold = 2005.0

    ex2 = thresh.apply(ex)
    
    s = flow.Stats2DView()
    s.by = "Dox"
    s.xchannel = "V2-A"
    s.xfunction = np.mean
    s.ychannel = "Y2-A"
    s.yfunction = np.mean
    s.huefacet = "Y2-A+"

    
    plt.ioff()
    s.plot(ex2)
    plt.show()
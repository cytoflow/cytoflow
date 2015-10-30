from __future__ import division

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasStrictTraits, Str, provides, Callable
import matplotlib.pyplot as plt

import numpy as np
import seaborn as sns
import pandas as pd

from cytoflow.views import IView
from cytoflow.utility import CytoflowViewError

@provides(IView)
class Stats2DView(HasStrictTraits):
    """
    Divide the data up by `variable`, then plot a scatter plot of a summary
    statistic `xfunction` on the x axis vs a summary statistic `yfunction` of
    the same data on the y axis.
    
    Attributes
    ----------
    name : Str
        The plot's name 
    
    variable : Str
        the name of the condition to put on the X axis
        
    xchannel : Str
        Apply `xfunction` to `xchannel` for each value of `xvariable`.
        
    xfunction : Callable
        What summary function to apply to `xchannel`
    
    ychannel : Str
        Apply `yfunction` to `ychannel` for each value of `variable`
        
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
    ...                                bin_width = 0.1)
    >>> view = flow.Stats2DView(name = "IFP vs OFP",
    ...                         variable = "IFP_Bin",
    ...                         xchannel = "Pacific Blue-A",
    ...                         xfunction = flow.geom_mean,
    ...                         ychannel = "FITC-A",
    ...                         yfunction = flow.geom_mean,
    ...                         huefacet = "CFP_Bin").plot(ex6_ifp_binned)
    >>> view.plot(ex_binned)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.stats2d"
    friendly_id = "2D Statistics View" 
    
    name = Str
    variable = Str
    xchannel = Str
    xfunction = Callable
    ychannel = Str
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
    
    # TODO - think carefully about transformed values.
    # ie, if we transform with Hlog, take the mean, then return the reverse
    # transformed mean, is that the same as taking the ... um .... geometric
    # mean of the untransformed data?  hm.
    
    def plot(self, experiment, **kwargs):
        """Plot a bar chart"""
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        if not self.variable:
            raise CytoflowViewError("Independent variable not set")
            
        if self.variable not in experiment.conditions:
            raise CytoflowViewError("Variable {0} not in the experiment"
                                    .format(self.variable))
        
        if not (experiment.conditions[self.variable] == "float" or
                experiment.conditions[self.variable] == "int"):
            raise CytoflowViewError("Variable {0} isn't numeric"
                                    .format(self.variable)) 
            
        if not self.xchannel:
            raise CytoflowViewError("X channel isn't set.")
        
        if self.xchannel not in experiment.channels:
            raise CytoflowViewError("X channel {0} isn't in the experiment"
                                    .format(self.xchannel))
        
        if not self.xfunction:
            raise CytoflowViewError("X summary function isn't set")
                
        if not self.ychannel:
            raise CytoflowViewError("Y channel isn't set.")
        
        if self.ychannel not in experiment.channels:
            raise CytoflowViewError("Y channel {0} isn't in the experiment"
                                    .format(self.ychannel))
        
        if not self.yfunction:
            raise CytoflowViewError("Y summary function isn't set")
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise CytoflowViewError("X facet {0} not in the experiment")
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise CytoflowViewError("Y facet {0} not in the experiment")
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise CytoflowViewError("Hue facet {0} not in the experiment")        

        kwargs.setdefault('antialiased', True)
        
        if self.subset:
            try:
                data = experiment.query(self.subset)
            except:
                raise CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
        else:
            data = experiment.data
            
        group_vars = [self.variable]
        if self.xfacet:
            group_vars.append(self.xfacet)
        if self.yfacet:
            group_vars.append(self.yfacet)
        if self.huefacet:
            group_vars.append(self.huefacet)
            
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
                             legend_out = False)

        grid.map(plt.plot, self.xchannel, self.ychannel, **kwargs)
        grid.add_legend()

    
if __name__ == '__main__':
    import cytoflow as flow
    import fcsparser

    tube1 = fcsparser.parse('../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                            reformat_meta = True)

    tube2 = fcsparser.parse('../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                            reformat_meta = True)
    
    tube3 = fcsparser.parse('../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                            reformat_meta = True)

    tube4 = fcsparser.parse('../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                            reformat_meta = True)
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float"})
    
    ex.add_tube(tube1, {"Dox" : 10.0})
    ex.add_tube(tube2, {"Dox" : 1.0})
#     ex.add_tube(tube3, {"Dox" : 10.0, "Repl" : 2})
#     ex.add_tube(tube4, {"Dox" : 1.0, "Repl" : 2})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['V2-A', 'Y2-A', 'B1-A', 'FSC-A', 'SSC-A']
    ex2 = hlog.apply(ex)
    
    thresh = flow.ThresholdOp()
    thresh.name = "Y2-A+"
    thresh.channel = 'Y2-A'
    thresh.threshold = 2005.0

    ex3 = thresh.apply(ex2)
    
    s = flow.Stats2DView()
    s.variable = "Dox"
    s.xchannel = "V2-A"
    s.xfunction = np.mean
    s.ychannel = "Y2-A"
    s.yfunction = np.mean
    s.huefacet = "Y2-A+"

    
    plt.ioff()
    s.plot(ex3)
    plt.show()
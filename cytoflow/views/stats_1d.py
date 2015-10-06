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

from cytoflow.views import IView
from cytoflow.utility import CytoflowViewError

@provides(IView)
class Stats1DView(HasStrictTraits):
    """
    Divide the data up by `variable`, then plot a line plot of `variable`
    on the x axis with a summary statistic `yfunction` of the same data in 
    `ychannel` on the y axis. 
    
    Attributes
    ----------
    name : Str
        The plot's name 
    
    variable : Str
        the name of the condition to put on the X axis

    ychannel : Str
        Apply `yfunction` to `ychannel` for each value of `variable`
        
    yfunction : Callable (list-like --> float)
        What summary function to apply to `ychannel`
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        
    yfacet : Str
        the conditioning variable for vertical subplots
        
    huefacet : 
        the conditioning variable for color.
        
    y_error_bars : Enum(None, "data", "summary")
        draw error bars?  if `data`, apply `y_error_function` to the same
        data that was summarized with `function`.  if `summary`, apply
        `y_error_function` to subsets defined by `y_error_var` 
        TODO - unimplemented
        
    y_error_var : Str
        the conditioning variable used to determine summary subsets.  take the
        data that was used to draw the bar; subdivide it further by 
        `y_error_var`; compute the summary statistic for each subset, then 
        apply `y_error_function` to the resulting list.  See the example.
        TODO - unimplemented
        
    y_error_function : Callable (list-like --> float)
        for each group/subgroup subset, call this function to compute the 
        error bars.  whether it is called on the data or the summary function
        is determined by the value of `y_error_bars`
        TODO - unimplemented
        
    subset : Str
        a string passed to Experiment.query() to subset the data before 
        we plot it.
        
    Examples
    --------
    
    Assume we want a Dox induction curve in a transient transfection experiment.  
    We have induced several wells with different amounts of Dox and the output
    of the Dox-inducible channel is "Pacific Blue-A".  We have a constitutive
    expression channel in "PE-Tx-Red-YG-A". We want to bin all the data by
    constitutive expression level, then plot the dose-response (geometric mean)
    curve in each bin. 
    
    >>> ex_binned = flow.BinningOp(name = "CFP_Bin",
    ...                            channel = "PE-Tx-Red-YG-A",
    ...                            scale = "log",
    ...                            bin_width = 0.1).apply(ex)
    >>> view = Stats1DView(name = "Dox vs IFP",
    ...                    variable = "Dox",
    ...                    ychannel = "Pacific Blue-A",
    ...                    huefacet = "CFP_Bin",
    ...                    yfunction = flow.geom_mean)
    >>> view.plot(ex_binned)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.stats1d"
    friendly_id = "1D Statistics View" 
    
    name = Str
    variable = Str
    ychannel = Str
    yfunction = Callable
    xfacet = Str
    yfacet = Str
    huefacet = Str
    
    # TODO - implement me pls?
#     y_error_bars = Enum(None, "data", "summary")
#     y_error_function = Callable
#     y_error_var = Str

    subset = Str
    
    # TODO - think carefully about how to handle transformations.
    # ie, if we transform with Hlog, take the mean, then return the reverse
    # transformed mean, is that the same as taking the ... um .... geometric
    # mean of the untransformed data?  or maybe just plot the appropriate
    # axes (ie the Y axis) with the transformed ticker?
    
    def plot(self, experiment, **kwargs):
        """Plot a bar chart"""
        
        if not self.variable:
            raise CytoflowViewError("Independent variable not set")
            
        if self.variable not in experiment.conditions:
            raise CytoflowViewError("Variable {0} not in the experiment"
                                    .format(self.variable))
        
        if not (experiment.conditions[self.variable] == "float" or
                experiment.conditions[self.variable] == "int"):
            raise CytoflowViewError("Variable {0} isn't numeric"
                                    .format(self.variable)) 

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
        
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)

        if self.subset:
            try:
                data = experiment.query(self.subset)
            except:
                raise 
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
        plot_data = g[self.ychannel].aggregate(self.yfunction).reset_index()        
  
        grid = sns.FacetGrid(plot_data,
                             col = (self.xfacet if self.xfacet else None),
                             row = (self.yfacet if self.yfacet else None),
                             hue = (self.huefacet if self.huefacet else None),
                             hue_order = (np.sort(plot_data[self.huefacet].unique())
                                          if self.huefacet else None),
                             legend_out = False)

        if 'repr' in experiment.metadata[self.variable] and \
            experiment.metadata[self.variable]['repr'] == 'log':
            plt.xscale('log', nonposx = 'mask')
        
        grid.map(plt.scatter, self.variable, self.ychannel, **kwargs)
        grid.map(plt.plot, self.variable, self.ychannel, **kwargs)
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
    
    s = flow.Stats1DView()
    s.variable = "Dox"
    s.ychannel = "Y2-A"
    s.yfunction = np.mean
    s.huefacet = "Y2-A+"
#    s.group = "Dox"
#    s.subgroup = "Y2-A+"
#    s.error_bars = "data"
    #s.error_var = "Repl"
#    s.error_function = np.std
    
    plt.ioff()
    s.plot(ex3)
    plt.show()
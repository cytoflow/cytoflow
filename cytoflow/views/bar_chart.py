from __future__ import division

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasTraits, Str, provides, Callable, Enum
import matplotlib.pyplot as plt
from cytoflow.views.i_view import IView
from cytoflow.views.sns_axisgrid import FacetGrid
from cytoflow.utility.util import num_hist_bins
import numpy as np
import seaborn as sns

@provides(IView)
class BarChartView(HasTraits):
    """Plots a bar chart of some summary statistic
    
    Attributes
    ----------
    name : Str
        The bar chart's name 
    
    channel : Str
        the name of the channel we're summarizing

    function : Callable (1D numpy.ndarray --> float)
        per facet, call this function to get the data.  takes a single
        parameter, a 1-dimensional numpy.ndarray, and returns a single float. 
        
    orientation : Enum("horizontal", "vertical")
        do we plot the bar chart horizontally or vertically?
        TODO - currently unimplemented
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        TODO - currently unimplemented
        
    yfacet : Str
        the conditioning variable for vertical subplots
        TODO - currently unimplemented
        
    group : Str
        the conditioning variable to group the chart's bars
        
    subgroup : Str
        the conditioning variable to make multiple bars in a group.  these
        subgroup bars are different colors.
        
    error : Str
        the conditioning variable to compute error bars.  ie, if you have
        three replicates and named the condition "replicate"
        
    error_function : Callable (2D numpy.ndarray --> 1D numpy.ndarray)
        for each group/subgroup subset, create a (n x 2) array where the
        first column is the observation and the second column is an int
        representing the replicate the 
        
    subset : Str
        a string passed to pandas.DataFrame.query() to subset the data before 
        we plot it.
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.histogram"
    friendly_id = "Histogram" 
    
    name = Str
    channel = Str
    function = Callable
    #orientation = Enum("horizontal", "vertical")
    xfacet = Str
    yfacet = Str
    group = Str
    subgroup = Str
    error = Str
    error_function = Callable
    subset = Str
    
    def plot(self, experiment, fig_num = None, **kwargs):
        """Plot a bar chart"""
        
        if not self.subset:
            x = experiment.data
        else:
            x = experiment.query(self.subset)
        
        if self.subgroup:
            g = experiment.data.groupby(by=[self.group, self.subgroup])
            agg = g[self.channel].aggregate(self.function)
            ngroup = len(agg.index.levels[0])
            nsubgroup = len(agg.index.levels[1])
            group_idx = np.arange(ngroup)
  
            bar_width = 0.35
            
            plt.ioff()
            colors = sns.color_palette("hls", nsubgroup)
            for i, subgroup in enumerate(agg.index.levels[1]):
                group_data = agg[:, subgroup]
                plt.bar(group_idx + i * bar_width,
                        group_data,
                        width = bar_width,
                        color = colors[i],
                        label = agg.index.names[1] + " = {0}".format(subgroup))
                
            group_names = ["{0} = {1}".format(self.group, x) for x in agg.index.levels[0]]
            plt.xticks(group_idx + bar_width, group_names)
            plt.legend()
            plt.show()
            plt.ion()
            
        else:
            g = experiment.data.groupby(by = [self.group])
            agg = g[self.channel].aggregate(self.function)
            ngroup = len(agg)
            group_idx = np.arange(ngroup)
            
            bar_width = 0.35
            colors = sns.color_palette("hls")
            
            plt.ioff()
            plt.bar(group_idx + bar_width,
                    agg,
                    width = bar_width,
                    color = colors[0])
            group_names = ["{0} = {1}".format(self.group, x) for x in agg.index]
            plt.xticks(group_idx + bar_width * 1.5, group_names)
            plt.legend()
            plt.show()
            plt.ion()
        
    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        if not experiment:
            return False
        
        if self.channel not in experiment.channels:
            return False
        
        if self.xfacet and self.xfacet not in experiment.metadata:
            return False
        
        if self.yfacet and self.yfacet not in experiment.metadata:
            return False
        
        if not self.group in experiment.metadata:
            return False
        
        if self.subgroup and not self.subgroup in experiment.metadata:
            return False
        
        if self.subset:
            try:
                experiment.query(self.subset)
            except:
                return False
        
        return True
    
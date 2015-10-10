from __future__ import division

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasStrictTraits, Str, provides
import matplotlib.pyplot as plt
from cytoflow.views import IView
from cytoflow.utility import num_hist_bins, CytoflowViewError
import numpy as np
import seaborn as sns

@provides(IView)
class HistogramView(HasStrictTraits):
    """Plots a one-channel histogram
    
    Attributes
    ----------
    name : Str
        The HistogramView name (for serialization, UI etc.)
    
    channel : Str
        the name of the channel we're plotting
    
    xfacet : Str 
        the conditioning variable for multiple plots (horizontal)
    
    yfacet : Str
        the conditioning variable for multiple plots (vertical)
    
    huefacet : Str
        the conditioning variable for multiple plots (color)
        
    subset : Str
        a string passed to pandas.DataFrame.query() to subset the data before 
        we plot it.
        
        .. note: Should this be a param instead?
        
    >>> hist = flow.HistogramView()
    >>> hist.name = "Histogram view, grid"
    >>> hist.channel = 'Y2-A'
    >>> hist.xfacet = 'Dox'
    >>> hist.yfacet = 'Y2-A+'
    >>> hist.plot(ex)
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.histogram"
    friendly_id = "Histogram" 
    
    name = Str
    channel = Str
    xfacet = Str
    yfacet = Str
    huefacet = Str
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        if self.channel not in experiment.channels:
            raise CytoflowViewError("Channel {0} not in the experiment"
                                    .format(self.channel))
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise CytoflowViewError("X facet {0} not in the experiment"
                                    .format(self.xfacet))
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise CytoflowViewError("Y facet {0} not in the experiment"
                                    .format(self.yfacet))
        
        if self.huefacet and self.huefacet not in experiment.conditions:
            raise CytoflowViewError("Hue facet {0} not in the experiment"
                                    .format(self.huefacet))

        if self.subset:
            try:
                data = experiment.query(self.subset)
            except:
                raise CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
        else:
            data = experiment.data        
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)

        num_bins = num_hist_bins(data[self.channel])
        xmin = np.amin(data[self.channel])
        xmax = np.amax(data[self.channel])
        bin_width = (xmax - xmin) / num_bins
        bins = np.arange(xmin, xmax, bin_width)
        kwargs.setdefault('bins', bins) 

        g = sns.FacetGrid(data, 
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),
                          legend_out = False)
        
        g.map(plt.hist, self.channel, **kwargs)
        g.add_legend()

    
if __name__ == '__main__':
   
    plt.ioff()
    p = plt.figure(1)

    tips = sns.load_dataset("tips")
    g = sns.FacetGrid(tips, col="time", fig_kws={"num" : 1})
    
    plt.show()
"""
Created on Apr 19, 2015

@author: brian
"""
from traits.api import HasStrictTraits, provides, Str

import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

from cytoflow.views import IView
from cytoflow.utility import CytoflowViewError

@provides(IView)
class ScatterplotView(HasStrictTraits):
    """
    Plots a 2-d scatterplot.  
    
    Attributes
    ----------
    
    name : Str
        The name of the plot, for visualization (and the plot title)
        
    xchannel : Str
        The channel to plot on the X axis
        
    ychannel : Str
        The channel to plot on the Y axis
        
    xfacet : Str
        The conditioning variable for multiple plots (horizontal)
        
    yfacet = Str
        The conditioning variable for multiple plots (vertical)
        
    huefacet = Str
        The conditioning variable for multiple plots (color)

    subset = Str
        A string passed to pandas.DataFrame.query() to subset the data before
        we plot it.
        
        .. note: should this be a param instead?
    """
    
    id = 'edu.mit.synbio.cytoflow.view.scatterplot'
    friend_id = "Scatter Plot"
    
    name = Str
    xchannel = Str
    ychannel = Str
    xfacet = Str
    yfacet = Str
    huefacet = Str
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted scatter plot view of a channel"""
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")

        if not self.xchannel:
            raise CytoflowViewError("X channel not specified")
        
        if self.xchannel not in experiment.channels:
            raise CytoflowViewError("X channel {0} not in the experiment"
                                    .format(self.xchannel))
            
        if not self.ychannel:
            raise CytoflowViewError("Y channel not specified")
        
        if self.ychannel not in experiment.channels:
            raise CytoflowViewError("Y channel {0} not in the experiment")
        
        if self.xfacet and self.xfacet not in experiment.conditions:
            raise CytoflowViewError("X facet {0} not in the experiment")
        
        if self.yfacet and self.yfacet not in experiment.conditions:
            raise CytoflowViewError("Y facet {0} not in the experiment")
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            raise CytoflowViewError("Hue facet {0} not in the experiment")
        
        if self.subset:
            try:
                data = experiment.query(self.subset)
            except:
                raise CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
        else:
            data = experiment.data
        
        kwargs.setdefault('alpha', 0.25)
        kwargs.setdefault('s', 2)
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)

        g = sns.FacetGrid(data, 
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          legend_out = False)
        
        g.map(plt.scatter, self.xchannel, self.ychannel, **kwargs)
        g.add_legend()
        #plt.rcdefaults()
        
if __name__ == '__main__':
    import cytoflow as flow
    import fcsparser
    
    mpl.rcParams['savefig.dpi'] = 2 * mpl.rcParams['savefig.dpi']
    
    tube1 = fcsparser.parse('../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                            reformat_meta = True)

    tube2 = fcsparser.parse('../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                            reformat_meta = True)
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float"})
    
    ex.add_tube(tube1, {"Dox" : 10.0})
    ex.add_tube(tube2, {"Dox" : 1.0})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['V2-A', 'Y2-A', 'B1-A', 'FSC-A', 'SSC-A']
    ex2 = hlog.apply(ex)
    
    thresh = flow.ThresholdOp()
    thresh.name = "Y2-A+"
    thresh.channel = 'Y2-A'
    thresh.threshold = 2005.0

    ex3 = thresh.apply(ex2)
    
    scatter = flow.ScatterplotView()
    scatter.name = "Scatter"
    scatter.xchannel = "FSC-A"
    scatter.ychannel = "SSC-A"
    scatter.huefacet = 'Dox'
    
    plt.ioff()
    scatter.plot(ex3)
    plt.show()
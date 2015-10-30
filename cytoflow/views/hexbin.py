"""
Created on Apr 19, 2015

@author: brian
"""
from traits.api import HasStrictTraits, provides, Str

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import matplotlib.transforms as mtrans

from cytoflow.views import IView
from cytoflow.utility import num_hist_bins, CytoflowViewError

@provides(IView)
class HexbinView(HasStrictTraits):
    """
    Plots a "hexbin" 2-d plot.  
    
    A hexbin is a 2-d histogram; the plot is divided into hexagons and the color
    of the hexagon is related to the number of points that fall into it.
    
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
    
    id = 'edu.mit.synbio.cytoflow.view.hexbin'
    friend_id = "Hex Bin"
    
    name = Str
    xchannel = Str
    ychannel = Str
    xfacet = Str
    yfacet = Str
    huefacet = Str
    subset = Str
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        if not self.xchannel:
            raise CytoflowViewError("X channel not specified")
        
#         exp_channels = [x for x in self.metadata 
#                         if 'type' in self.metadata[x] 
#                         and self.metadata[x]['type'] == "channel"]
        
        if self.xchannel not in experiment.data:
            raise CytoflowViewError("X channel {0} not in the experiment"
                                    .format(self.xchannel))
            
        if not self.ychannel:
            raise CytoflowViewError("Y channel not specified")
        
        if self.ychannel not in experiment.data:
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
                raise CytoflowViewError("Subset string \'{0}\' not valid")
        else:
            data = experiment.data
        
        #kwargs.setdefault('histtype', 'stepfilled')
        #kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('edgecolor', 'none')
        #kwargs.setdefault('mincnt', 1)
        #kwargs.setdefault('bins', 'log')
        kwargs.setdefault('antialiased', True)
            
        xmin, xmax = (np.amin(data[self.xchannel]), np.amax(data[self.xchannel]))
        ymin, ymax = (np.amin(data[self.ychannel]), np.amax(data[self.ychannel]))
        # to avoid issues with singular data, expand the min/max pairs
        xmin, xmax = mtrans.nonsingular(xmin, xmax, expander=0.1)
        ymin, ymax = mtrans.nonsingular(ymin, ymax, expander=0.1)
        
        extent = (xmin, xmax, ymin, ymax)
        kwargs.setdefault('extent', extent)
        
        xbins = num_hist_bins(experiment[self.xchannel])
        ybins = num_hist_bins(experiment[self.ychannel])
        bins = np.mean([xbins, ybins])
        
        kwargs.setdefault('bins', bins) # Do not move above.  don't ask.

        g = sns.FacetGrid(data,
                          size = 6,
                          aspect = 1.5, 
                          col = (self.xfacet if self.xfacet else None),
                          row = (self.yfacet if self.yfacet else None),
                          hue = (self.huefacet if self.huefacet else None),
                          col_order = (np.sort(data[self.xfacet].unique()) if self.xfacet else None),
                          row_order = (np.sort(data[self.yfacet].unique()) if self.yfacet else None),
                          hue_order = (np.sort(data[self.huefacet].unique()) if self.huefacet else None),)
        
        g.map(plt.hexbin, self.xchannel, self.ychannel, **kwargs)
        
if __name__ == '__main__':
    import cytoflow as flow
    import fcsparser
    
    import matplotlib as mpl
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
    
    hexbin = flow.HexbinView()
    hexbin.name = "Hex"
    hexbin.xchannel = "FSC-A"
    hexbin.ychannel = "SSC-A"
    hexbin.huefacet = 'Dox'
    
    plt.ioff()
    hexbin.plot(ex2)
    plt.show()
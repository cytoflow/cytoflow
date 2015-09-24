"""
Created on Apr 19, 2015

@author: brian
"""
from traits.api import HasStrictTraits, provides, Str
from cytoflow.views.i_view import IView
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns

@provides(IView)
class ScatterplotView(HasStrictTraits):
    """
    classdocs
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
    
    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        if not experiment:
            return False
        
        if not self.xchannel or self.xchannel not in experiment.channels:
            return False
        
        if not self.ychannel or self.ychannel not in experiment.channels:
            return False
        
        if self.xfacet and self.xfacet not in experiment.metadata:
            return False
        
        if self.yfacet and self.yfacet not in experiment.metadata:
            return False
        
        if self.huefacet and self.huefacet not in experiment.metadata:
            return False
        
        if self.subset:
            try:
                experiment.query(self.subset)
            except:
                return False
        
        return True
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted scatter plot view of a channel"""
        
        kwargs.setdefault('alpha', 0.25)
        kwargs.setdefault('s', 2)
        kwargs.setdefault('marker', 'o')
        kwargs.setdefault('antialiased', True)

        
        if not self.subset:
            x = experiment.data
        else:
            x = experiment.query(self.subset)

        g = sns.FacetGrid(x, 
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
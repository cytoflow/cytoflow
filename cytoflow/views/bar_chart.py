from __future__ import division

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasStrictTraits, Str, provides, Callable
import matplotlib.pyplot as plt
from cytoflow.views.i_view import IView
import numpy as np
import seaborn as sns

@provides(IView)
class BarChartView(HasStrictTraits):
    """Plots a bar chart of some summary statistic
    
    Attributes
    ----------
    name : Str
        The bar chart's name 
    
    channel : Str
        the name of the channel we're summarizing 
        
    variable : Str
        the name of the conditioning variable to group the chart's bars

    function : Callable (1D numpy.ndarray --> float)
        per facet, call this function to summarize the data.  takes a single
        parameter, a 1-dimensional numpy.ndarray, and returns a single float. 
        useful suggestions: np.mean, cytoflow.geom_mean
        
    error_bars : Enum(None, "data", "summary")
        draw error bars?  if "data", apply *error_function* to the same
        data that was summarized with *function*.  if "summary", apply
        *function* to subsets defined by *error_var*  
        TODO - unimplemented
        
    error_var : Str
        the conditioning variable used to determine summary subsets.  take the
        data that was used to draw the bar; subdivide it further by error_var;
        compute the summary statistic for each subset, then apply error_function
        to the resulting list.
        TODO - unimplemented
        
    error_function : Callable (1D numpy.ndarray --> float)
        for each group/subgroup subset, call this function to compute the 
        error bars.  whether it is called on the data or the summary function
        is determined by the value of *error_bars*
        TODO - unimplemented
        
    xfacet : Str
        the conditioning variable for horizontal subplots
        
    yfacet : Str
        the conditioning variable for vertical subplots
        
    huefacet : Str
        the conditioning variable to make multiple bar colors
        
    orientation : Enum("horizontal", "vertical")
        do we plot the bar chart horizontally or vertically?
        TODO - waiting on seaborn v0.6

    subset : Str
        a string passed to pandas.DataFrame.query() to subset the data before 
        we plot it.
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.barchart"
    friendly_id = "Bar Chart" 
    
    name = Str
    channel = Str
    variable = Str
    function = Callable
#    orientation = Enum("horizontal", "vertical")
    xfacet = Str
    yfacet = Str
    huefacet = Str
    # TODO - make error bars work properly.
#     error_bars = Enum(None, "data", "summary")
#     error_function = Callable
#     error_var = Str
    subset = Str
    
    # TODO - return the un-transformed values?  is this even valid?
    # ie, if we transform with Hlog, take the mean, then return the reverse
    # transformed mean, is that the same as taking the ... um .... geometric
    # mean of the untransformed data?  hm.
    
    def plot(self, experiment, **kwargs):
        """Plot a bar chart"""
        
        if self.subset:
            data = experiment.query(self.subset)
        else:
            data = experiment.data
            
        plot = sns.factorplot(x = self.variable,
                              y = self.channel,
                              data = data,
                              row = (self.yfacet if self.yfacet else None),
                              col = (self.xfacet if self.xfacet else None),
                              hue = (self.huefacet if self.huefacet else None),
                              #orient = ("h" if self.orientation == "horizontal" 
                              #          else "v"),
                              # TODO - when seaborn releases 0.6, depend on it
                              # and use the orient flag
                              estimator = self.function,
                              ci = None,
                              kind = "bar")
        
        
#         if self.subgroup:
#             g = x.groupby(by=[self.group, self.subgroup])
#             agg = g[self.channel].aggregate(self.function)
#             
#             if self.error_bars == "data":
#                 err_bars = g[self.channel].aggregate(self.error_function)
#             elif self.error_bars == "summary":
#                 error_g = x.groupby(by = [self.group, self.subgroup, self.error_var])
#                 error_agg = error_g[self.channel].aggregate(self.function)
#                 err_bars = error_agg.groupby(level = [self.group, self.subgroup]) \
#                                 .aggregate(self.error_function)
#             else:
#                 err_bars = None
# 
#             ngroup = len(agg.index.levels[0])
#             nsubgroup = len(agg.index.levels[1])
#             group_idx = np.arange(ngroup)
#   
#             bar_width = 0.35
# 
#             plt.figure()
#             colors = sns.color_palette("hls", nsubgroup)
#             for i, subgroup in enumerate(agg.index.levels[1]):
#                 group_data = agg[:, subgroup]
#                 group_err_bars = err_bars[:, subgroup].as_matrix() \
#                                  if err_bars else None
# 
#                 plt.bar(group_idx + i * bar_width,
#                         group_data,
#                         width = bar_width,
#                         color = colors[i],
#                         yerr = group_err_bars,
#                         label = agg.index.names[1] + " = {0}".format(subgroup))
#                 
#             group_names = ["{0} = {1}".format(self.group, x) for x in agg.index.levels[0]]
#             plt.xticks(group_idx + bar_width, group_names)
#             plt.legend()
# 
#         else:
#             g = x.groupby(by = [self.group])
#             agg = g[self.channel].aggregate(self.function)
#             
#             if self.error_bars == "data":
#                 err_bars = g[self.channel].aggregate(self.error_function).as_matrix()
#             elif self.error_bars == "summary":
#                 error_g = x.groupby(by = [self.group, self.error_var])
#                 error_agg = error_g[self.channel].aggregate(self.error_function)
#                 err_bars = error_agg.groupby(level = self.error_var) \
#                                 .aggregate(self.error_function)  \
#                                 .as_matrix()
#             else:
#                 err_bars = None    
#             ngroup = len(agg)
#             group_idx = np.arange(ngroup)
#             
#             bar_width = 0.35
#             colors = sns.color_palette("hls")
#             
#             plt.figure()
#             plt.bar(group_idx + bar_width,
#                     agg,
#                     width = bar_width,
#                     yerr = err_bars,
#                     color = colors[0])
#             group_names = ["{0} = {1}".format(self.group, x) for x in agg.index]
#             plt.xticks(group_idx + bar_width * 1.5, group_names)
#             plt.legend()
        
    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        if not experiment:
            return False
        
        if self.channel not in experiment.channels:
            return False
        
        if not self.variable in experiment.metadata:
            return False
        
        if not self.function:
            return False
        
        if self.xfacet and self.xfacet not in experiment.metadata:
            return False
        
        if self.yfacet and self.yfacet not in experiment.metadata:
            return False

        if self.huefacet and self.huefacet not in experiment.metadata:
            return False
        
#         if self.error_bars == 'data' and self.error_function is None:
#             return False
#         
#         if self.error_bars == 'summary' \
#             and (self.error_function is None 
#                  or not self.error_var in experiment.metadata):
#             return False
        
        if self.subset:
            try:
                experiment.query(self.subset)
            except:
                return False
        
        return True
    
if __name__ == '__main__':
    import cytoflow as flow
    import FlowCytometryTools as fc
    
    tube1 = fc.FCMeasurement(ID='Test 1', 
                             datafile='../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')

    tube2 = fc.FCMeasurement(ID='Test 2', 
                           datafile='../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    tube3 = fc.FCMeasurement(ID='Test 3', 
                             datafile='../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')

    tube4 = fc.FCMeasurement(ID='Test 4', 
                           datafile='../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float", "Repl" : "int"})
    
    ex.add_tube(tube1, {"Dox" : 10.0, "Repl" : 1})
    ex.add_tube(tube2, {"Dox" : 1.0, "Repl" : 1})
    ex.add_tube(tube3, {"Dox" : 10.0, "Repl" : 2})
    ex.add_tube(tube4, {"Dox" : 1.0, "Repl" : 2})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['V2-A', 'Y2-A', 'B1-A', 'FSC-A', 'SSC-A']
    ex2 = hlog.apply(ex)
    
    thresh = flow.ThresholdOp()
    thresh.name = "Y2-A+"
    thresh.channel = 'Y2-A'
    thresh.threshold = 2005.0

    ex3 = thresh.apply(ex2)
    
    s = flow.BarChartView()
    s.channel = "V2-A"
    s.function = flow.geom_mean
    s.variable = "Dox"
    s.huefacet = "Y2-A+"
    #s.error_bars = "data"
    #s.error_var = "Repl"
    s.error_function = np.std
    
    plt.ioff()
    s.plot(ex3)
    plt.show()
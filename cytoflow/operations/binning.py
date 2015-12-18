'''
Created on Sep 18, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, Enum, provides, Undefined, \
    Instance, DelegatesTo, Constant
import numpy as np

from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError, CytoflowViewError, \
    PositiveInt, PositiveFloat
from cytoflow.views.histogram import HistogramView
from cytoflow.views import IView

@provides(IOperation)
class BinningOp(HasStrictTraits):
    """
    Bin data along an axis.
    
    This operation creates equally spaced bins (in linear or log space)
    along an axis and adds a metadata column assigning each event to a bin.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by apply()
        
    channel : Str
        The name of the channel along which to bin.
        
    num_bins = Int
        The number of bins to make.  Must set either `num_bins` or `bin_width`.
        If both are defined, `num_bins` takes precedence.
        
    bin_width = Float
        The width of the bins.  Must set either `num_bins` or `bin_width`.  If
        `scale` is `log10`, `bin_width` is in log-10 units.  If both `num_bins`
        and `bin_width` are defined, `num_bins` takes precedence. 
        
    scale : Enum("linear", "log10")
        Make the bins equidistant along what scale?
        TODO - add other scales, like Logicle      
        
    bin_count_name : Str
        If `bin_count_name` is set, add another piece of metadata when calling
        `apply()` that contains the number of events in the bin that this event
        falls in.  Useful for filtering bins by # of events.
        
    Examples
    --------
    >>> bin_op = flow.BinningOp(name = "CFP_Bin",
    ...                         channel = "PE-Tx-Red-YG-A",
    ...                         scale = "linear",
    ...                         num_bins = 40)
    >>> ex5_binned = bin_op.apply(ex5)

    >>> h.huefacet = "CFP_Bin"
    >>> h.plot(ex5_binned)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.binning')
    friendly_id = Constant("Binning")
    
    name = CStr()
    bin_count_name = CStr()
    channel = Str()
    num_bins = PositiveInt(Undefined)
    bin_width = PositiveFloat(Undefined)
    scale = Enum("linear", "log10")

    def apply(self, experiment):
        """Applies the binning to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment, the same as old_experiment but with a new
            column the same as the operation name.  The bool is True if the
            event's measurement in self.channel is greater than self.low and
            less than self.high; it is False otherwise.
        """
        if not experiment:
            raise CytoflowOpError("no experiment specified")
        
        if not self.name:
            raise CytoflowOpError("name is not set")
        
        if self.name in experiment.data.columns:
            raise CytoflowOpError("name {0} is in the experiment already"
                                  .format(self.name))
            
        if self.bin_count_name and self.bin_count_name in experiment.data.columns:
            raise CytoflowOpError("bin_count_name {0} is in the experiment already"
                                  .format(self.bin_count_name))
        
        if not self.channel:
            raise CytoflowOpError("channel is not set")
        
        if self.channel not in experiment.data.columns:
            raise CytoflowOpError("channel {0} isn't in the experiment"
                                  .format(self.channel))
              
        if self.num_bins is Undefined and self.bin_width is Undefined:
            raise CytoflowOpError("must set either bin number or width")  
            
        channel_min = experiment.data[self.channel].min()
        channel_max = experiment.data[self.channel].max()
        
        if self.scale == "linear":
            num_bins = self.num_bins if self.num_bins is not Undefined else \
                       (channel_max - channel_min) / self.bin_width
            bins = np.linspace(start = channel_min, stop = channel_max,
                               num = num_bins)
        elif self.scale == "log10":
            channel_min = channel_min if channel_min > 0 else 1
            num_bins = self.num_bins if self.num_bins is not Undefined else \
                       (np.log10(channel_max) - np.log10(channel_min)) / self.bin_width
            bins = np.logspace(start = np.log10(channel_min),
                               stop = np.log10(channel_max),
                               num = num_bins,
                               base = 10) 
            
        # bins need to be internal; drop the first and last one
        bins = bins[1:-1]
            
        new_experiment = experiment.clone()
        new_experiment[self.name] = np.digitize(experiment[self.channel], bins)
        
        new_experiment.conditions[self.name] = "int"
        new_experiment.metadata[self.name] = {}
        new_experiment.metadata[self.name]["bins"] = bins
        
        if self.bin_count_name:
            # TODO - this is a HUGE memory hog?!
            agg_count = new_experiment.data.groupby(self.name).count()
            agg_count = agg_count[agg_count.columns[0]]
            new_experiment[self.bin_count_name] = \
                new_experiment[self.name].map(agg_count)
            new_experiment.conditions[self.bin_count_name] = "int"
            new_experiment.metadata[self.bin_count_name] = {}
        
        return new_experiment
    
    def default_view(self):
        return BinningView(op = self)
    
@provides(IView)
class BinningView(HistogramView):
    """Plots a histogram of the current binning op, with the bins set to
       the hue facet.
       
    Attributes
    ----------
    op: Instance(BinningOp)
        the BinningOp we're viewing
       
    subset : Str
        The string passed to `Experiment.query()` to subset the data before
        plotting
        
    Examples
    --------
    >>> b = BinningOp(name = "Y2-A-Bin",
    ...               channel = "Y2-A",
    ...               num_bins = 10,
    ...               scale = "linear")
    >>> b.default_view().plot(ex2)
    """
     
    id = Constant('edu.mit.synbio.cytoflow.views.binning')
    friendly_id = Constant('Binning Setup')
    
    op = Instance(IOperation)   
    name = DelegatesTo('op')
    channel = DelegatesTo('op')
    huefacet = DelegatesTo('op', 'name')
    
    def plot(self, experiment, **kwargs):
        if not self.huefacet:
            raise CytoflowViewError("didn't set BinningOp.name")
        
        try:
            temp_experiment = self.op.apply(experiment)
            super(BinningView, self).plot(temp_experiment, **kwargs)
        except CytoflowOpError as e:
            raise CytoflowViewError(e.__str__())

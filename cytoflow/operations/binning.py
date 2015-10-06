'''
Created on Sep 18, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, Int, Enum, Float, provides
import numpy as np

from cytoflow.operations import IOperation
from cytoflow.utility import CytoflowOpError

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
        The number of bins to make.  Must set either `num_bins` or `bin_width`
        
    bin_width = Float
        The width of the bins.  Must set either `num_bins` or `bin_width`
        
    scale : Enum("Linear", "Log")
        Make the bins equidistant along what scale?
        TODO - add other scales, like Logicle      
        
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
    id = "edu.mit.synbio.cytoflow.operations.binning"
    friendly_id = "Binning"
    
    name = CStr()
    channel = Str()
    num_bins = Int(None)
    bin_width = Float(None)
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

        if not self.name:
            raise CytoflowOpError("You have to set the Binning operations's name "
                                  "before applying it!")
        
        if self.name in experiment.data.columns:
            raise CytoflowOpError("Operation name is in the experiment already!")
        
        if not self.channel:
            raise CytoflowOpError("Didn't specify a channel")
        
        if not self.channel in experiment.channels:
            raise CytoflowOpError("channel isn't in the experiment")
              
        if not self.num_bins and not self.bin_width:
            raise CytoflowOpError("Must set either bin number or width")
        
        if self.num_bins and self.num_bins <= 0:
            raise CytoflowOpError("Number of bins must be positive")
        
        if self.bin_width and self.bin_width <= 0:
            raise CytoflowOpError("Bin width must be positive")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise CytoflowOpError("Experiment already contains a column {0}"
                               .format(self.name))    
            
        channel_min = experiment.data[self.channel].min()
        channel_max = experiment.data[self.channel].max()
        
        if self.scale == "linear":
            num_bins = self.num_bins if self.num_bins else \
                       (channel_max - channel_min) / self.bin_width
            bins = np.linspace(start = channel_min, stop = channel_max,
                               num = num_bins)
        elif self.scale == "log10":
            num_bins = self.num_bins if self.num_bins else \
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
        
        return new_experiment
        
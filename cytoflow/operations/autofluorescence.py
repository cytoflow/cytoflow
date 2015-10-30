from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, CFloat, File, Dict, \
                       Instance, List, Constant, provides
import numpy as np
import fcsparser

from cytoflow.operations import IOperation
from cytoflow.views import IView
from cytoflow.utility import CytoflowOpError
from cytoflow.utility.util import CytoflowOpError

@provides(IOperation)
class AutofluorescenceOp(HasStrictTraits):
    """
    Apply autofluorescence correction to a set of fluorescence channels.
    
    The `estimate()` function loads a separate FCS file (not part of the input
    `Experiment`) and computes the untransformed median and standard deviation 
    of the blank cells.  Then, `apply()` subtracts the median from the 
    experiment data.
    
    To use, set the `blank_file` property to point to an FCS file with
    unstained or nonfluorescing cells in it; set the `channels` property to a 
    list of channels to correct; and call `estimate()`, then `apply()`.
    
    `apply()` also adds the "af_median" and "af_stdev" metadata to the corrected
    channels, representing the median and standard deviation of the measured 
    blank distributions.  Some other modules (especially in the TASBE workflow)
    depend on this metadata and will fail if it's not present.
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation; optional for interactive use)
        
    channels : List(Str)
        The channels to correct.
        
    blank_file : File
        The filename of a file with "blank" cells (not fluorescent).  Used
        to `estimate()` the autofluorescence.
        
    Examples
    --------
    >>> af_op = flow.AutofluorescenceOp()
    >>> af_op.blank_file = "blank.fcs"
    >>> af_op.channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"] 

    >>> af_op.estimate(ex)
    >>> af_op.default_view().plot()
    >>> ex2 = af_op.apply(ex)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.autofluorescence')
    friendly_id = Constant("Autofluorescence correction")
    
    name = CStr()
    channels = List(Str)
    blank_file = File(filter = "*.fcs", exists = True, transient = True)

    _af_median = Dict(Str, CFloat)
    _af_stdev = Dict(Str, CFloat)
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the autofluorescence from *blank_file*
        """
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        exp_channels = [x for x in experiment.metadata 
                        if 'type' in experiment.metadata[x] 
                        and experiment.metadata[x]['type'] == "channel"]

        if not set(self.channels) <= set(exp_channels):
            raise CytoflowOpError("Specified channels that weren't found in "
                                  "the experiment.")

        # don't have to validate that blank_file exists; should crap out on 
        # trying to set a bad value
        
        try:
            blank_meta, blank_data = \
                fcsparser.parse(self.blank_file, reformat_meta = True)  
            blank_channels = blank_meta["_channels_"].set_index("$PnN")     
        except Exception as e:
            raise CytoflowOpError("FCS reader threw an error: " + e.value)
        
        for channel in self.channels:
            if (channel not in experiment.metadata
                or 'voltage' not in experiment.metadata[channel]):
                raise CytoflowOpError("Didn't find voltage for channel {0}"
                                      .format(channel))
                
            v = experiment.metadata[channel]['voltage']
            
            if not "$PnV" in blank_channels.ix[channel]:
                raise CytoflowOpError("Didn't find a voltage for channel {0}"
                                      "in tube {1}"
                                      .format(channel, self.blank_file))
            
            blank_v = blank_channels.ix[channel]['$PnV']
            
            if blank_v != v:
                raise CytoflowOpError("Voltage differs for channel {0}".format(channel)) 
       
        for channel in self.channels:
            self._af_median[channel] = np.median(blank_data[channel])
            self._af_stdev[channel] = np.std(blank_data[channel])    
                
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment with the autofluorescence median subtracted from
            the values in self.blank_file
        """
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        exp_channels = [x for x in experiment.metadata 
                        if 'type' in experiment.metadata[x] 
                        and experiment.metadata[x]['type'] == "channel"]
        
        if not set(self._af_median.keys()) <= set(exp_channels) or \
           not set(self._af_stdev.keys()) <= set(exp_channels):
            raise CytoflowOpError("Autofluorescence estimates aren't set, or are "
                               "different than those in the experiment "
                               "parameter. Did you forget to run estimate()?")

        if not set(self._af_median.keys()) == set(self._af_stdev.keys()):
            raise CytoflowOpError("Median and stdev keys are different! "
                               "What the hell happened?!")
        
        if not set(self.channels) == set(self._af_median.keys()):
            raise CytoflowOpError("Estimated channels differ from the channels "
                               "parameter.  Did you forget to (re)run estimate()?")
        
        new_experiment = experiment.clone()
                
        for channel in self.channels:
            new_experiment[channel] = \
                experiment[channel] - self._af_median[channel]
                
            # add the AF values to the channel's metadata, so we can correct
            # other controls (etc) later on
            new_experiment.metadata[channel]['af_median'] = \
                self._af_median[channel]
                
            new_experiment.metadata[channel]['af_stdev'] = \
                self._af_stdev[channel]

        return new_experiment
    
    def default_view(self):
        return AutofluorescenceDiagnosticView(op = self)
    
    
@provides(IView)
class AutofluorescenceDiagnosticView(HasStrictTraits):
    """
    Plots a histogram of each channel, and its median in red.  Serves as a
    diagnostic for the autofluorescence correction.
    
    
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
    
    op : Instance(AutofluorescenceOp)
        The op whose parameters we're viewing
        
    """
    
    # traits   
    id = Constant('edu.mit.synbio.cytoflow.view.autofluorescencediagnosticview')
    friendly_id = Constant("Autofluorescence Diagnostic")
    
    name = Str
    op = Instance(IOperation)
    
    def plot(self, experiment = None, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
        
        _, blank_data = fcsparser.parse(self.op.blank_file, reformat_meta=True)    
        plt.figure()
        
        for idx, channel in enumerate(self.op.channels):
            d = blank_data[channel]
            plt.subplot(len(self.op.channels), 1, idx+1)
            plt.title(channel)
            plt.hist(d, bins = 200, **kwargs)
            
            plt.axvline(self.op._af_median[channel], color = 'r')

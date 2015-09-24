from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, CFloat, File, Dict, \
                       Instance, List, provides
import numpy as np
from cytoflow.operations.i_operation import IOperation
import FlowCytometryTools as fc
from ..views import IView

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
    >>> af_op.is_valid(ex)
    >>> af_op.default_view().plot()
    >>> ex2 = af_op.apply(ex)
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.autofluorescence"
    friendly_id = "Autofluorescence correction"
    
    name = CStr()
    channels = List(Str)
    af_median = Dict(Str, CFloat)
    af_stdev = Dict(Str, CFloat)
    
    blank_file = File(filter = "*.fcs", exists = True, transient = True)
    
    def is_valid(self, experiment):
        """Validate this operation against an experiment."""

        if not self.name:
            return False
        
        if not set(self.af_median.keys()) <= set(experiment.channels):
            return False
        
        if not set(self.af_stdev.keys()) <= set(experiment.channels):
            return False
        
        if not set(self.af_median.keys()) == set(self.af_stdev.keys()):
            return False
        
        if not set(self.channels) == set(self.af_median.keys()):
            return False

        return True
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the autofluorescence from *blank_file*
        """
        
        if not set(self.channels) <= set(experiment.channels):
            raise RuntimeError("Specified bad channels")

        # don't have to validate that blank_file exists; should crap out on 
        # trying to set a bad value
        
        blank_tube = fc.FCMeasurement(ID="blank", datafile = self.blank_file)

        # make sure that the blank tube was collected with the same voltages
        # as the experimental tubes

        try:
            blank_tube.read_meta()
        except Exception:
            raise RuntimeError("FCS reader threw an error!")
        
        for channel in self.channels:
            v = experiment.metadata[channel]['voltage']
            
            if not "$PnV" in blank_tube.channels:
                raise RuntimeError("Didn't find a voltage for channel {0}" \
                                   "in tube {1}".format(channel, blank_tube.datafile))
            
            blank_v = blank_tube.channels[blank_tube.channels['$PnN'] == channel]['$PnV'].iloc[0]
            
            if blank_v != v:
                raise RuntimeError("Voltage differs for channel {0}".format(channel)) 
       
        for channel in self.channels:
            self.af_median[channel] = np.median(blank_tube.data[channel])
            self.af_stdev[channel] = np.std(blank_tube.data[channel])    
                
    def apply(self, old_experiment):
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
        
        new_experiment = old_experiment.clone()
                
        for channel in self.channels:
            new_experiment[channel] = \
                old_experiment[channel] - self.af_median[channel]
                
            # add the AF values to the channel's metadata, so we can correct
            # other controls (etc) later on
            new_experiment.metadata[channel]['af_median'] = \
                self.af_median[channel]
                
            new_experiment.metadata[channel]['af_stdev'] = \
                self.af_stdev[channel]

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
    id = "edu.mit.synbio.cytoflow.view.autofluorescencediagnosticview"
    friendly_id = "Autofluorescence Diagnostic" 
    
    name = Str
    op = Instance(IOperation)
    
    def plot(self, experiment = None, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
        
        tube = fc.FCMeasurement(ID="blank", datafile = self.op.blank_file)    
        plt.figure()
        
        for idx, channel in enumerate(self.op.channels):
            d = tube.data[channel]
            plt.subplot(len(self.op.channels), 1, idx+1)
            plt.title(channel)
            plt.hist(d, bins = 200, **kwargs)
            
            plt.axvline(self.op.af_median[channel], color = 'r')
                    
    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        
        return self.op.is_valid(experiment)

    


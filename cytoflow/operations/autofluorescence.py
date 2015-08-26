from traits.api import HasStrictTraits, Str, CStr, CFloat, File, Dict, Instance, Python
import numpy as np
import matplotlib as mpl
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation
import FlowCytometryTools as fc
from ..views import IView

@provides(IOperation)
class AutofluorescenceOp(HasStrictTraits):
    """
    Apply autofluorescence correction to a set of fluorescence channels.
    
    If using known autofluorescence values, simply set up the *autofluorescence*
    dict and then apply().
    
    If estimating, set up the *autofluorescence* dict with the channels to
    estimate and arbitrary values; set the *blank_file* property, and call
    *estimate()*.
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation.)
        
    autofluorescence : Dict(Str, Float)
        The channel names to correct, and the corresponding autoflorescence
        values.
        
    blank_file : File
        The filename of a file with "blank" cells (not fluorescing).
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.autofluorescence"
    friendly_id = "Polygon"
    
    name = CStr()
    autofluorescence = Dict(Str, CFloat)
    blank_file = File(filter = "*.fcs", exists = True)
    
    def is_valid(self, experiment):
        """Validate this operation against an experiment."""

        if not self.name:
            return False
        
        if not set(self.autofluorescence.keys()).issubset(set(experiment.channels)):
            return False
        
        # don't have to validate that blank_file exists; should crap out on 
        # trying to set a bad value
        
        if self.blank_file is not None:
            tube = fc.FCMeasurement(ID="blank", datafile = self.blank_file)
            
            try:
                tube.read_meta()
            except Exception:
                print "FCS reader threw an error!"
                return False
            
            for channel in self.autofluorescence.keys():
                v = experiment.metadata[channel]['voltage']
                
                if not "$PnV" in tube.channels:
                    raise RuntimeError("Didn't find a voltage for channel {0}" \
                                       "in tube {1}".format(channel, tube.datafile))
                
                blank_v = tube.channels[tube.channels['$PnN'] == channel]['$PnV'].iloc[0]
                
                if blank_v != v:
                    return False
            
        # TODO - make sure there haven't been transformations applied to 
        # the channels yet!
       
        return True
    
    def estimate(self, experiment = None, subset = None): 
        """
        Estimate the autofluorescence from *blank_file*
        """
        
        tube = fc.FCMeasurement(ID="blank", datafile = self.blank_file)
                
        for channel in self.autofluorescence.keys():
            self.autofluorescence[channel] = np.median(tube.data[channel])     
               
        
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
                
        for channel in self.autofluorescence.keys():
            new_experiment[channel] = old_experiment[channel] - \
                                      self.autofluorescence[channel]

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
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
        
        tube = fc.FCMeasurement(ID="blank", datafile = self.op.blank_file)    
        plt.figure()
        channels = self.op.autofluorescence.keys()
        
        for idx, channel in enumerate(channels):
            d = tube.data[channel]
            plt.subplot(len(channels), 1, idx+1)
            plt.title(channel)
            plt.hist(d, bins = 200)
            
            plt.axvline(self.op.autofluorescence[channel], color = 'r')
                    
    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        
        return self.op.is_valid(experiment)

    


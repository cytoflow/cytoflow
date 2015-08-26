from traits.api import HasStrictTraits, Str, CStr, List, Float, File
import numpy as np
import matplotlib as mpl
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation
import FlowCytometryTools as fc

@provides(IOperation)
class AutofluorescenceOp(HasStrictTraits):
    """Apply autofluorescence correction to a set of fluorescence channels.
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation.)
        
    channels : List(Str)
        The name of the first channel to apply the range gate.
        
    blank_file : File
        The filename of a file with "blank" cells (not fluorescing).
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.autofluorescence"
    friendly_id = "Polygon"
    
    name = CStr()
    channels = List(Str)
    blank_file = File(filter = "*.fcs", exists = True)
    
    def is_valid(self, experiment):
        """Validate this operation against an experiment."""

        if not self.name:
            return False
        
        if not set(self.channels).issubset(set(experiment.channels)):
            return False
        
        # don't have to validate that blank_file exists; should crap out on 
        # trying to set a bad value
        
        tube = fc.FCMeasurement(ID="blank", datafile = self.blank_file)
        
        try:
            tube.read_meta()
        except Exception:
            print "FCS reader threw an error!"
            return False
        
        for channel in self.channels:
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
        
        tube = fc.FCMeasurement(ID="blank", datafile = self.blank_file)
        new_experiment = old_experiment.clone()
                
        for channel in self.channels:
            blank_median = np.median(tube.data[channel])
            new_experiment[channel] = old_experiment[channel] - blank_median

        return new_experiment

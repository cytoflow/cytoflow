from __future__ import division

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasStrictTraits, Str, provides, List, File
import matplotlib.pyplot as plt
from cytoflow.views.i_view import IView
from cytoflow.utility.util import num_hist_bins
import numpy as np
import seaborn as sns
import FlowCytometryTools as fc

@provides(IView)
class AutofluorescenceDiagnosticView(HasStrictTraits):
    """
    Plots a histogram of each channel, and its median in red.  Serves as a
    diagnostic for the autofluorescence correction.
    
    
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
    
    channels : List(Str)
        the names of the channel we're plotting
    
    blank_file : File
        The filename of the file with the 'blank' cells.
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.autofluorescencediagnosticview"
    friendly_id = "Autofluorescence Diagnostic" 
    
    name = Str
    channels = List(Str)
    blank_file = File(filter = "*.fcs", exists = True)
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
        
        tube = fc.FCMeasurement(ID="blank", datafile = self.blank_file)    
        plt.figure()
        num_channels = len(self.channels)
        
        for idx, channel in enumerate(self.channels):
            d = tube.data[channel]
            #num_bins = num_hist_bins(d) / 4
            plt.subplot(num_channels, 1, idx+1)
            plt.title(channel)
            plt.hist(d, bins = 200)
            
            median = np.median(d)
            plt.axvline(median, color = 'r')
                    
    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        
        if not experiment:
            return False
        
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
            v = experiment.metadata[channel]
            
            if not "$PnV" in tube.channels:
                raise RuntimeError("Didn't find a voltage for channel {0}" \
                                   "in tube {1}".format(channel, tube.datafile))
            
            blank_v = tube.channels[tube.channels['$PnN'] == channel]['$PnV'].iloc[0]
            
            if blank_v != v:
                return False
            
        # TODO - make sure there haven't been transformations applied to 
        # the channels yet!
        
        return True
    
if __name__ == '__main__':
   
    plt.ioff()
    p = plt.figure(1)

    tips = sns.load_dataset("tips")
    g = sns.FacetGrid(tips, col="time", fig_kws={"num" : 1})
    
    plt.show()
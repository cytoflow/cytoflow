'''
Created on Aug 26, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Python, Instance, \
                       Int
import numpy as np
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation
import FlowCytometryTools as fc

from ..views import IView

@provides(IOperation)
class BleedthroughPiecewiseOp(HasStrictTraits):
    """
    Apply bleedthrough correction to a set of fluorescence channels.
    
    To use, set up the `controls` dict with the single color controls; 
    call `estimate()` to populate `bleedthrough`; check that the bleedthrough 
    plots look good with `default_view`(); and then `apply()` to an Experiment.
    
    **WARNING THIS CODE IS WILDLY INEFFICIENT AND TAKES A VERY LONG TIME**
    **TODO - MAKE MORE EFFICIENT please**
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation.)
        
    bleedthrough : Dict(Str, Dict(Str, scipy.interpolate.LSQUnivariateSpline))
        The splines to do the bleedthrough correction.  The first key is
        the source channel; the second key is the destination channel; and
        and the value is the spline representing the bleedthrough.  So,
        ``bleedthrough['FITC-A']['PE-A']`` is the bleedthrough *from* the
        `FITC-A` channel *to* the `PE-A` channel.
        
    voltage : Dict(Str, Int)
        The channel voltages that the single-color controls were collected at.
        This gets persisted by pickle(); while `controls` and `knots` don't,
        they're to parameterize `estimate()`.
        
    controls : Dict(Str, File)
        The channel names to correct, and corresponding single-color control
        FCS files to estimate the correction splines with.  Must be set to
        use `estimate()`.
        
    num_knots : Int (default = 5)
        The number of internal control points to estimate, spaced log-evenly
        from 0 to the range of the channel.  Must be set to use `estimate()`.
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.bleedthrough_piecewise"
    friendly_id = "Piecewise Bleedthrough Correction"
    
    name = CStr()

    bleedthrough = Dict(Dict(Str, Python))
    voltage = Dict(Str, Int)
    
    controls = Dict(Str, File, transient = True)
    knots = Int(5, transient = True)
    
    def is_valid(self, experiment):
        """Validate this operation against an experiment."""

        if not self.name:
            return False
        
        # NOTE: these conditions are for applying the correction, NOT estimating
        # the correction from controls.
        
        if not self.bleedthrough:
            return False
        
        if not set(self.bleedthrough.keys()).issubset(set(experiment.channels)):
            return False
        
        # make sure the controls were collected with the same voltages as
        # the experiment
        
        for channel, voltage in self.voltage.iteritems():
            if experiment.metadata[channel]['voltage'] != voltage:
                return False
       
        return True
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the bleedthrough from the single-channel controls in `controls`
        """
        
        channels = self.controls.keys()
        
        # make sure the voltages are all in order
        for channel in channels:       
            tube = fc.FCMeasurement(ID="blank", datafile = self.controls[channel])
            
            try:
                tube.read_meta()
            except Exception:
                raise RuntimeError("FCS reader threw an error on tube {0}".format(self.controls[channel]))

            for channel in channels:
                exp_v = experiment.metadata[channel]['voltage']
            
                if not "$PnV" in tube.channels:
                    raise RuntimeError("Didn't find a voltage for channel {0}" \
                                       "in tube {1}".format(channel, tube.datafile))
                
                control_v = tube.channels[tube.channels['$PnN'] == channel]['$PnV'].iloc[0]
                
                if control_v != exp_v:
                    raise RuntimeError("Voltage differs for channel {0} in tube {1}"
                                       .format(channel, self.controls[channel]))
            
            self.voltage[channel] = experiment.metadata[channel]['voltage']

        self.bleedthrough = {}

        for from_channel in channels:
            self.bleedthrough[from_channel] = {}
            
            tube = fc.FCMeasurement(ID="blank", datafile = self.controls[from_channel])
            range = experiment.metadata[from_channel]['range']
            knots = np.logspace(1, )
            
            for to_channel in channels:
                if channel == to_channel:
                    continue
                
               
        
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
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """
        
        return 
        
@provides(IView)
class BleedthroughPiecewiseDiagnostic(HasStrictTraits):
    """
    Plots a scatterplot of each channel vs every other channel and the 
    bleedthrough spline
    
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
    
    op : Instance(BleedthroughPiecewiseOp)
        The op whose parameters we're viewing
        
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.autofluorescencediagnosticview"
    friendly_id = "Autofluorescence Diagnostic" 
    
    name = Str
    
    # TODO - why can't I use BleedthroughPiecewiseOp here?
    op = Instance(IOperation)
    
    def plot(self, experiment = None, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        import matplotlib.pyplot as plt
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
         
        plt.figure()
                    
    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        
        return self.op.is_valid(experiment)

    


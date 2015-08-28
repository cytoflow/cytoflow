'''
Created on Aug 26, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, CInt, File, Dict, Python, \
                       Instance, Int, CFloat
import numpy as np
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation
import FlowCytometryTools as fc
import math
import scipy.interpolate
import scipy.optimize

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
        
    blank_file : File
    
    controls : Dict(Str, File)
        The channel names to correct, and corresponding single-color control
        FCS files to estimate the correction splines with.  Must be set to
        use `estimate()`.
        
    num_knots : Int (default = 7)
        The number of internal control points to estimate, spaced log-evenly
        from 0 to the range of the channel.  Must be set to use `estimate()`.
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.bleedthrough_piecewise"
    friendly_id = "Piecewise Bleedthrough Correction"
    
    name = CStr()

    bleedthrough = Dict(Str, Dict(Str, Python))
    voltage = Dict(Str, CInt)
    
    blank_file = File
    controls = Dict(Str, File, transient = True)
    num_knots = Int(5, transient = True)
    
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

        if self.num_knots < 3:
            raise RuntimeError("Need to allow at least 3 knots in the spline")
        
        channels = self.controls.keys()
        
        # make sure the voltages are all in order
        
        blank_tube = fc.FCMeasurement(ID='blank', datafile = self.blank_file)
        
        try:
            blank_tube.read_meta()
        except Exception:
            raise RuntimeError("FCS reader threw an error on tube {0}".format(self.blank_file))

        for channel in channels:
            exp_v = experiment.metadata[channel]['voltage']
        
            if not "$PnV" in blank_tube.channels:
                raise RuntimeError("Didn't find a voltage for channel {0}" \
                                   "in tube {1}".format(channel, blank_tube.datafile))
            
            control_v = blank_tube.channels[blank_tube.channels['$PnN'] == channel]['$PnV'].iloc[0]
            
            if control_v != exp_v:
                raise RuntimeError("Voltage differs for channel {0} in tube {1}"
                                   .format(channel, self.controls[channel]))
    
        for channel in channels:       
            tube = fc.FCMeasurement(ID=channel, datafile = self.controls[channel])
            
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

        blank_af = {}
        for channel in channels:
            blank_af[channel] = np.median(blank_tube.data[channel])

        self.bleedthrough = {}

        for from_channel in channels:
            self.bleedthrough[from_channel] = {}
            
            tube = fc.FCMeasurement(ID=from_channel, datafile = self.controls[from_channel])
            data = tube.data.sort(from_channel)
            
            # i'm not sure about this -- but it cleans up the plots wonderfully
            for channel in channels:
                #data = data[data[channel] > 1]
                data[channel] = data[channel] - blank_af[channel]

            channel_min = data[from_channel].min()
            channel_max = data[from_channel].max()

            r = experiment.metadata[from_channel]['range']
            knots = np.logspace(1, math.log(r, 2), num=self.num_knots, base = 2)
            knots = [k for k in knots if k > channel_min and k < channel_max]
            
            for to_channel in channels:
                if from_channel == to_channel:
                    continue
                
                self.bleedthrough[from_channel][to_channel] = \
                    scipy.interpolate.LSQUnivariateSpline(data[from_channel].values,
                                                          data[to_channel].values,
                                                          t = knots,
                                                          k = 1)
                    
                # TODO - some sort of validity checking.

    def apply(self, old_experiment):
        """Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment with the bleedthrough subtracted out.
        """
        
        def correct_bleedthrough(row, channels):
            idx = {channel : idx for idx, channel in enumerate(channels)}
            
            def err_channel(x, channel):
                ret = row[channel] - x[idx[channel]]
                for from_channel in [c for c in channels if c != channel]:
                    ret -= self.bleedthrough[from_channel][channel] \
                                            (x[idx[from_channel]])
                return ret
            
            def err_bld(x):
                ret = [err_channel(x, channel) for channel in channels]
                return ret
            
            x_0 = row.loc[channels].convert_objects(convert_numeric = True)
            x = scipy.optimize.root(err_bld, x_0)
            
            ret = row.copy()
            for idx, channel in enumerate(channels):
                ret[channel] = x.x[idx]
                
            return ret
        
        channels = self.bleedthrough.keys()
        old_data = old_experiment.data[channels].copy()
        new_data = old_data.apply(correct_bleedthrough, axis = 1, args = ([channels]))
                
        new_experiment = old_experiment.clone()
        for channel in channels:
            new_experiment[channel] = new_data[channel]

        return new_experiment
    
    def default_view(self):
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """
        
        if set(self.controls.keys()) != set(self.bleedthrough.keys()):
            raise "Must have both the controls and bleedthrough to plot" 
 
        channels = self.controls.keys()
        
        # make sure we can get the control tubes to plot the diagnostic
        for channel in channels:       
            tube = fc.FCMeasurement(ID=channel, datafile = self.controls[channel])
            
            try:
                tube.read_meta()
            except Exception:
                raise RuntimeError("FCS reader threw an error on tube {0}".format(self.controls[channel]))
        
        return BleedthroughPiecewiseDiagnostic(op = self)
        
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
        
        channels = self.op.bleedthrough.keys()
        num_channels = len(channels)
        
        for from_idx, from_channel in enumerate(channels):
            for to_idx, to_channel in enumerate(channels):
                if from_idx == to_idx:
                    continue

                tube = fc.FCMeasurement(ID=from_channel, 
                                        datafile = self.op.controls[from_channel])
                
                                
                plt.subplot(num_channels, 
                            num_channels, 
                            from_idx + (to_idx * num_channels) + 1)
                plt.xscale('log', nonposx='mask')
                plt.yscale('log', nonposy='mask')
                plt.xlabel(from_channel)
                plt.ylabel(to_channel)
                plt.scatter(tube.data[from_channel],
                            tube.data[to_channel],
                            alpha = 0.1,
                            s = 1,
                            marker = 'o')
                
                spline = self.op.bleedthrough[from_channel][to_channel]
                xs = np.logspace(-1, math.log(tube.data[from_channel].max(), 10))
            
                plt.plot(xs, 
                         spline(xs), 
                         'g-', 
                         lw=3)

    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        
        return self.op.is_valid(experiment)

    


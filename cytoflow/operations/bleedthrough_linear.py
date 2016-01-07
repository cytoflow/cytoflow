'''
Created on Aug 26, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Python, \
                       Instance, Int, List, Constant, Tuple, Float, provides
    
import numpy as np
import math
import os
import warnings
import scipy.interpolate
import scipy.optimize
import pandas
import fcsparser

import matplotlib.pyplot as plt

from cytoflow.operations.i_operation import IOperation
from cytoflow.operations.hlog import hlog, hlog_inv
from cytoflow.views import IView
from cytoflow.utility import CytoflowOpError, cartesian
from piston_mini_client import returns

@provides(IOperation)
class BleedthroughLinearOp(HasStrictTraits):
    """
    Apply matrix-based bleedthrough correction to a set of fluorescence channels.
    
    This is a traditional matrix-based compensation for bleedthrough.  For each
    pair of channels, the user specifies the proportion of the first channel
    that bleeds through into the second; then, the module performs a matrix
    multiplication to compensate the raw data.
    
    The module can also estimate the bleedthrough matrix using one
    single-color control per channel.
    
    This works best on data that has had autofluorescence removed first;
    if that is the case, then the autofluorescence will be subtracted from
    the single-color controls too.
    
    To use, set up the `controls` dict with the single color controls;
    call `estimate()` to parameterize the operation; check that the bleedthrough 
    plots look good with `default_view().plot()`; and then `apply()` to an 
    Experiment.
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation; optional for interactive use)
    
    controls : Dict(Str, File)
        The channel names to correct, and corresponding single-color control
        FCS files to estimate the correction splines with.  Must be set to
        use `estimate()`.
        
    spillover : Dict(Tuple(Str, Str), Float)
        The spillover "matrix" to use to correct the data.  The keys are pairs
        of channels, and the values are proportions of spectral overlap.  If 
        `("channel1", "channel2")` is present as a key, 
        `("channel2", "channel1")` must also be present.  The module does not
        assume that the matrix is symmetric.
        
    Notes
    -----


    Examples
    --------
    >>> bl_op = flow.BleedthroughLinearOp()
    >>> bl_op.controls = {'Pacific Blue-A' : 'merged/ebfp.fcs',
    ...                   'FITC-A' : 'merged/eyfp.fcs',
    ...                   'PE-Tx-Red-YG-A' : 'merged/mkate.fcs'}
    >>>
    >>> bl_op.estimate(ex2)
    >>> bl_op.default_view().plot(ex2)    
    >>>
    >>> ex3 = bl_op.apply(ex2)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.bleedthrough_linear')
    friendly_id = Constant("Linear Bleedthrough Correction")
    
    name = CStr()

    controls = Dict(Str, File)
    spillover = Dict(Tuple(Str, Str), Float)
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the bleedthrough from simgle-channel controls in `controls`
        """
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        channels = self.controls.keys()

        if len(channels) < 2:
            raise CytoflowOpError("Need at least two channels to correct bleedthrough.")

        # make sure the control files exist
        for channel in channels:
            if not os.path.isfile(self.controls[channel]):
                raise CytoflowOpError("Can't find file {0} for channel {1}."
                                      .format(self.controls[channel], channel))
                
        # try to read the tube and check its channels and voltages
        for channel in channels:
            try:
                channel_naming = experiment.metadata["name_meta"]
                tube_meta = fcsparser.parse(self.controls[channel], 
                                            meta_data_only = True, 
                                            reformat_meta = True,
                                            channel_naming = channel_naming)
                tube_channels = tube_meta["_channels_"].set_index("$PnN")
            except Exception as e:
                raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(self.controls[channel], str(e)))

            for channel in channels:
                exp_v = experiment.metadata[channel]['voltage']
            
                if not "$PnV" in tube_channels.ix[channel]:
                    raise CytoflowOpError("Didn't find a voltage for channel {0}" 
                                          "in tube {1}".format(channel, self.controls[channel]))
                
                control_v = tube_channels.ix[channel]["$PnV"]
                
                if control_v != exp_v:
                    raise CytoflowOpError("Voltage differs for channel {0} in tube {1}"
                                          .format(channel, self.controls[channel]))
                    
        for channel in channels:
            try:
                channel_naming = experiment.metadata["name_meta"]
                tube_meta, tube_data = \
                    fcsparser.parse(self.controls[channel], 
                                    reformat_meta = True,
                                    channel_naming = channel_naming)
                tube_channels = tube_meta["_channels_"].set_index("$PnN")
            except Exception as e:
                raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(self.controls[channel], str(e)))
            
            data = tube_data.sort(channel)

            for af_channel in channels:
                if 'af_median' in experiment.metadata[af_channel]:
                    data[af_channel] = data[af_channel] - \
                                    experiment.metadata[af_channel]['af_median']
            
            for to_channel in channels:
                from_channel = channel
                
                if from_channel == to_channel:
                    continue
                
                # sometimes some of the data is off the edge of the
                # plot, and this screws up a linear regression
                
                # TODO - do a better job figuring out (and excluding)
                # off-axis data
                from_5, from_95 = np.percentile(data[from_channel], (5, 95))
                data = data[data[from_channel] > from_5]
                data = data[data[from_channel] < from_95]
                
                to_5, to_95 = np.percentile(data[to_channel], (5, 95))
                data = data[data[to_channel] > to_5]
                data = data[data[to_channel] < to_95]
                
                data.reset_index(drop = True, inplace = True)
                
                lr = np.polyfit(data[from_channel],
                                data[to_channel],
                                deg = 1)
                
                self.spillover[(from_channel, to_channel)] = lr[0]
                
    def apply(self, experiment):
        """Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment with the bleedthrough subtracted out.
        """
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        if not self.spillover:
            raise CytoflowOpError("Spillover matrix isn't set. "
                                  "Did you forget to run estimate()?")
        
        for (from_channel, to_channel) in self.spillover:
            if not from_channel in experiment.data:
                raise CytoflowOpError("Can't find channel {0} in experiment"
                                      .format(from_channel))
            if not to_channel in experiment.data:
                raise CytoflowOpError("Can't find channel {0} in experiment"
                                      .format(to_channel))
                
            if not (to_channel, from_channel) in self.spillover:
                raise CytoflowOpError("Must have both (from, to) and "
                                      "(to, from) keys in self.spillover")
        
        new_experiment = experiment.clone()
        
        # the completely arbitrary ordering of the channels
        channels = list(set([x for (x, _) in self.spillover.keys()]))
        
        # build the spillover matrix from the spillover dictionary
        a = [  [self.spillover[(y, x)] if x != y else 1.0 for x in channels]
               for y in channels]
        
        # invert it.  use the pseudoinverse in case a is singular
        a_inv = np.linalg.pinv(a)
        
        new_experiment.data[channels] = np.dot(experiment.data[channels], a_inv)
        
        for channel in channels:
            # add the spillover values to the channel's metadata
            new_experiment.metadata[channel]['linear_bleedthrough'] = \
                {x : self.spillover[(x, channel)]
                     for x in channels if x != channel}
        
        return new_experiment
    
    def default_view(self):
        """
        Returns a diagnostic plot to make sure spillover estimation is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """
 
        # the completely arbitrary ordering of the channels
        channels = list(set([x for (x, _) in self.spillover.keys()]))
        
        if set(self.controls.keys()) != set(channels):
            raise CytoflowOpError("Must have both the controls and bleedthrough to plot")
        
        # make sure we can get the control tubes to plot the diagnostic
        for channel in channels:       
            try:
                # suppress the channel name warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                
                    _ = fcsparser.parse(self.controls[channel], 
                                        meta_data_only = True, 
                                        reformat_meta = True)
            except Exception as e:
                raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(self.controls[channel], str(e)))

        return BleedthroughLinearDiagnostic(op = self)
    
@provides(IView)
class BleedthroughLinearDiagnostic(HasStrictTraits):
    """
    Plots a scatterplot of each channel vs every other channel and the 
    bleedthrough line
    
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
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
         
        plt.figure()
        
        # the completely arbitrary ordering of the channels
        channels = list(set([x for (x, _) in self.op.spillover.keys()]))
        num_channels = len(channels)
        
        for from_idx, from_channel in enumerate(channels):
            for to_idx, to_channel in enumerate(channels):
                if from_idx == to_idx:
                    continue
                
                try:
                    channel_naming = experiment.metadata["name_meta"]
                    _, tube_data = \
                        fcsparser.parse(self.op.controls[from_channel], 
                                        reformat_meta = True,
                                        channel_naming = channel_naming)
                except Exception as e:
                    raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                          .format(self.op.controls[from_channel], str(e)))
             
                plt.subplot(num_channels, 
                            num_channels, 
                            from_idx + (to_idx * num_channels) + 1)
                plt.xlim(np.percentile(tube_data[from_channel], (5, 95)))
                plt.ylim(np.percentile(tube_data[to_channel], (5, 95)))
                plt.xlabel(from_channel)
                plt.ylabel(to_channel)
                plt.scatter(tube_data[from_channel],
                            tube_data[to_channel],
                            alpha = 0.1,
                            s = 1,
                            marker = 'o')
                
                xstart, xstop = np.percentile(tube_data[from_channel], (5, 95))
                xs = np.linspace(xstart, xstop, 10)
                ys = xs * self.op.spillover[(from_channel, to_channel)]
          
                plt.plot(xs, ys, 'g-', lw=3)

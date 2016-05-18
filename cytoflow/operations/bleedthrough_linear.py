#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Aug 26, 2015

@author: brian
'''

from __future__ import division, absolute_import

import os

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Instance, \
                       Constant, Tuple, Float, provides
    
import numpy as np
import matplotlib.pyplot as plt

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation
from .import_op import Tube, ImportOp, check_tube

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
            raise util.CytoflowOpError("No experiment specified")
        
        channels = self.controls.keys()

        if len(channels) < 2:
            raise util.CytoflowOpError("Need at least two channels to correct bleedthrough.")

        # make sure the control files exist
        for channel in channels:
            if not os.path.isfile(self.controls[channel]):
                raise util.CytoflowOpError("Can't find file {0} for channel {1}."
                                      .format(self.controls[channel], channel))
                
        for channel in channels:
            
            # make a little Experiment
            check_tube(self.controls[channel], experiment)
            tube_exp = ImportOp(tubes = [Tube(file = self.controls[channel])],
                                name_metadata = experiment.metadata['name_metadata']).apply()
            
            # apply previous operations
            for op in experiment.history:
                tube_exp = op.apply(tube_exp)
                
            # subset it
            if subset:
                try:
                    tube_data = tube_exp.query(subset)
                except:
                    raise util.CytoflowOpError("Subset string '{0}' isn't valid"
                                          .format(self.subset))
                                
                if len(tube_data.index) == 0:
                    raise util.CytoflowOpError("Subset string '{0}' returned no events"
                                          .format(self.subset))
            else:
                tube_data = tube_exp.data
                
            # polyfit requires sorted data
            tube_data.sort(channel, inplace = True)

            for to_channel in channels:
                from_channel = channel
                
                if from_channel == to_channel:
                    continue
                
                # sometimes some of the data is off the edge of the
                # plot, and this screws up a linear regression
                
                from_min = np.min(tube_data[from_channel]) * 1.05
                from_max = np.max(tube_data[from_channel]) * 0.95
                tube_data = tube_data[tube_data[from_channel] > from_min]
                tube_data = tube_data[tube_data[from_channel] < from_max]
                
                to_min = np.min(tube_data[to_channel]) * 1.05
                to_max = np.max(tube_data[to_channel]) * 0.95
                tube_data = tube_data[tube_data[to_channel] > to_min]
                tube_data = tube_data[tube_data[to_channel] < to_max]
                
                tube_data.reset_index(drop = True, inplace = True)
                
                lr = np.polyfit(tube_data[from_channel],
                                tube_data[to_channel],
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
            raise util.CytoflowOpError("No experiment specified")
        
        if not self.spillover:
            raise util.CytoflowOpError("Spillover matrix isn't set. "
                                  "Did you forget to run estimate()?")
        
        for (from_channel, to_channel) in self.spillover:
            if not from_channel in experiment.data:
                raise util.CytoflowOpError("Can't find channel {0} in experiment"
                                      .format(from_channel))
            if not to_channel in experiment.data:
                raise util.CytoflowOpError("Can't find channel {0} in experiment"
                                      .format(to_channel))
                
            if not (to_channel, from_channel) in self.spillover:
                raise util.CytoflowOpError("Must have both (from, to) and "
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
     
        new_experiment.history.append(self.clone_traits())   
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to make sure spillover estimation is working.
        
        Returns
        -------
        IView : An IView, call plot() to see the diagnostic plots
        """
 
        # the completely arbitrary ordering of the channels
        channels = list(set([x for (x, _) in self.spillover.keys()]))
        
        if set(self.controls.keys()) != set(channels):
            raise util.CytoflowOpError("Must have both the controls and bleedthrough to plot")

        return BleedthroughLinearDiagnostic(op = self, **kwargs)
    
@provides(cytoflow.views.IView)
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
        
        if not experiment:
            raise util.CytoflowOpError("No experiment specified")
        
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
                
                check_tube(self.op.controls[from_channel], experiment)
                tube_exp = ImportOp(tubes = [Tube(file = self.op.controls[from_channel])],
                                    name_metadata = experiment.metadata['name_metadata']).apply()
                
                # apply previous operations
                for op in experiment.history:
                    tube_exp = op.apply(tube_exp)
                    
                tube_data = tube_exp.data

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
                xs = np.linspace(xstart, xstop, 2)
                ys = xs * self.op.spillover[(from_channel, to_channel)]
          
                plt.plot(xs, ys, 'g-', lw=3)
                
        plt.tight_layout(pad = 0.8)

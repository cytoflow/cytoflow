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

import math

from traits.api import (HasStrictTraits, Str, CStr, File, Dict, Python,
                        Instance, Int, List, Constant, provides)
import numpy as np
import scipy.interpolate
import scipy.optimize
import pandas

import matplotlib.pyplot as plt

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation
from .hlog import hlog, hlog_inv
from .import_op import Tube, ImportOp, check_tube, parse_tube

@provides(IOperation)
class BleedthroughPiecewiseOp(HasStrictTraits):
    """
    Apply bleedthrough correction to a set of fluorescence channels.
    
    This is not a traditional bleedthrough matrix-based compensation; it uses
    a similar set of single-color controls, but instead of computing a compensation
    matrix, it fits a piecewise-linear spline to the untransformed data and
    uses those splines to compute the correction factor at each point in
    a mesh across the color space.  The experimental data is corrected using
    a linear interpolation along that mesh: this is much faster than computing
    the correction factor for each cell indiviually (an operation that takes
    5 msec each.)
    
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
        
    num_knots : Int (default = 7)
        The number of internal control points to estimate, spaced log-evenly
        from 0 to the range of the channel.  Must be set to use `estimate()`.
        
    mesh_size : Int (default = 32)
        The size of each axis in the mesh used to interpolate corrected values.
        
    Notes
    -----
    We use an interpolation-based scheme to estimate corrected bleedthrough.
    The algorithm is as follows:
    
     - Fit a piecewise-linear spline to each single-color control's bleedthrough
       into other channels.  Because we want to fit the spline to untransfomed
       data, but capture both the negative, positive-linear and positive-log 
       portions of a traditional flow data set, we distribute the spline knots 
       evenly on an hlog-transformed axis for each color we're correcting.   

     - At each point on a regular mesh spanning the entire range of the
       instrument, estimate the mapping from (raw colors) --> (actual colors).
       The mesh points are also distributed evenly along the hlog-transformed
       color axes; this captures negative data as well as positive 
       This is quite slow: ~30 seconds for a mesh size of 32 in 3-space.
       Remember that additional channels expand the number of mesh points
       exponentially!

     - Use these estimates to paramaterize a linear interpolator (in linear
       space, this time).  There's one interpolator per output channel (so
       for a 3-channel correction, each interpolator is R^3 --> R).  For 
       each measured cell, run each interpolator to give the corrected output.

    Examples
    --------
    >>> bl_op = flow.BleedthroughPiecewiseOp()
    >>> bl_op.num_knots = 10
    >>> bl_op.controls = {'Pacific Blue-A' : 'merged/ebfp.fcs',
    ...                   'FITC-A' : 'merged/eyfp.fcs',
    ...                   'PE-Tx-Red-YG-A' : 'merged/mkate.fcs'}
    >>>
    >>> bl_op.estimate(ex2)
    >>> bl_op.default_view().plot(ex2)    
    >>>
    >>> %time ex3 = bl_op.apply(ex2) # 410,000 cells
    CPU times: user 577 ms, sys: 27.7 ms, total: 605 ms
    Wall time: 607 ms
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.bleedthrough_piecewise')
    friendly_id = Constant("Piecewise Bleedthrough Correction")
    
    name = CStr()

    controls = Dict(Str, File)
    num_knots = Int(7)
    mesh_size = Int(32)

    _splines = Dict(Str, Dict(Str, Python))
    _interpolators = Dict(Str, Python)
    
    # because the order of the channels is important, we can't just call
    # _interpolators.keys()
    # TODO - this is ugly and unpythonic.  :-/
    _channels = List(Str)
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the bleedthrough from the single-channel controls in `controls`
        """
        if not experiment:
            raise util.CytoflowOpError("No experiment specified")
        
        if self.num_knots < 3:
            raise util.CytoflowOpError("Need to allow at least 3 knots in the spline")
        
        self._channels = self.controls.keys()

        if len(self._channels) < 2:
            raise util.CytoflowOpError("Need at least two channels to correct bleedthrough.")

        self._splines = {}
        mesh_axes = []

        for channel in self._channels:
            self._splines[channel] = {}
            
            # make a little Experiment
            check_tube(self.controls[channel], experiment)
            tube_exp = ImportOp(tubes = [Tube(file = self.controls[channel])]).apply()
            
            # apply previous operations
            for op in experiment.history:
                tube_exp = op.apply(tube_exp)
                
            # subset it
            if subset:
                try:
                    tube_data = tube_exp.query(subset).copy()
                except:
                    raise util.CytoflowOpError("Subset string '{0}' isn't valid"
                                          .format(self.subset))
                                
                if len(tube_data.index) == 0:
                    raise util.CytoflowOpError("Subset string '{0}' returned no events"
                                          .format(self.subset))
            else:
                tube_data = tube_exp.data.copy()
                
            # polyfit requires sorted data
            tube_data.sort_values(by = channel, inplace = True)
            
            channel_min = tube_data[channel].min()
            channel_max = tube_data[channel].max()
            
            # we're going to set the knots and splines evenly across the hlog-
            # transformed data, so as to capture both the "linear" aspect
            # of near-0 and negative values, and the "log" aspect of large
            # values

            # parameterize the hlog transform
            r = experiment.metadata[channel]['range']  # instrument range
            d = np.log10(r)  # maximum display scale, in decades
            
            # the transition point from linear --> log scale
            # use half of the log-transformed scale as "linear".
            b = 2 ** (np.log2(r) / 2)
            
            # the splines' knots
            knot_min = channel_min
            knot_max = channel_max
            
            hlog_knot_min, hlog_knot_max = \
                hlog((knot_min, knot_max), b = b, r = r, d = d)
            hlog_knots = np.linspace(hlog_knot_min, hlog_knot_max, self.num_knots)
            knots = hlog_inv(hlog_knots, b = b, r = r, d = d)
            
            # only keep the interior knots
            knots = knots[1:-1] 
            
            # the interpolators' mesh       
            if 'af_median' in experiment.metadata[channel] and \
               'af_stdev' in experiment.metadata[channel]:     
                mesh_min = experiment.metadata[channel]['af_median'] - \
                           3 * experiment.metadata[channel]['af_stdev']
            else:
                mesh_min = -0.01 * r  # TODO - does this even work?
                
            mesh_max = r
                
            hlog_mesh_min, hlog_mesh_max = \
                hlog((mesh_min, mesh_max), b = b, r = r, d = d)
            hlog_mesh_axis = \
                np.linspace(hlog_mesh_min, hlog_mesh_max, self.mesh_size)
            
            mesh_axis = hlog_inv(hlog_mesh_axis, b = b, r = r, d = d)
            mesh_axes.append(mesh_axis)
            
            for to_channel in self._channels:
                from_channel = channel
                if from_channel == to_channel:
                    continue
                
                self._splines[from_channel][to_channel] = \
                    scipy.interpolate.LSQUnivariateSpline(tube_data[from_channel].values,
                                                          tube_data[to_channel].values,
                                                          t = knots,
                                                          k = 1)
         
        
        mesh = pandas.DataFrame(util.cartesian(mesh_axes), 
                                columns = [x for x in self._channels])
         
        mesh_corrected = mesh.apply(_correct_bleedthrough,
                                    axis = 1,
                                    args = ([[x for x in self._channels], 
                                             self._splines]))
        
        for channel in self._channels:
            chan_values = np.reshape(mesh_corrected[channel], [len(x) for x in mesh_axes])
            self._interpolators[channel] = \
                scipy.interpolate.RegularGridInterpolator(points = mesh_axes, 
                                                          values = chan_values, 
                                                          bounds_error = False, 
                                                          fill_value = 0.0)

        # TODO - some sort of validity checking.

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
        
        if not self._interpolators:
            raise util.CytoflowOpError("Module interpolators aren't set. "
                                  "Did you run estimate()?")
            
        if not set(self._interpolators.keys()) <= set(experiment.channels):
            raise util.CytoflowOpError("Module parameters don't match experiment channels")

        new_experiment = experiment.clone()
        
        # get rid of data outside of the interpolators' mesh 
        # (-3 * autofluorescence sigma)
        for channel in self._channels:     
            
            # if you update the mesh calculation above, update it here too!
            if 'af_median' in experiment.metadata[channel] and \
               'af_stdev' in experiment.metadata[channel]:     
                mesh_min = experiment.metadata[channel]['af_median'] - \
                           3 * experiment.metadata[channel]['af_stdev']
            else:
                mesh_min = -0.01 * experiment.metadata[channel]['range']  # TODO - does this even work?

            new_experiment.data = \
                new_experiment.data[new_experiment.data[channel] > mesh_min]
        
        new_experiment.data.reset_index(drop = True, inplace = True)
        
        old_data = new_experiment.data[self._channels]
        
        for channel in self._channels:
            new_experiment[channel] = self._interpolators[channel](old_data)
            
            # add the correction splines to the experiment metadata so we can 
            # correct other controls later on
            new_experiment.metadata[channel]['piecewise_bleedthrough'] = \
                (self._channels, self._interpolators[channel])

        new_experiment.history.append(self.clone_traits())
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """
        
        if set(self.controls.keys()) != set(self._splines.keys()):
            raise util.CytoflowOpError("Must have both the controls and bleedthrough to plot")

        return BleedthroughPiecewiseDiagnostic(op = self, **kwargs)
    
# module-level "static" function (doesn't require a class instance)
def _correct_bleedthrough(row, channels, splines):
    idx = {channel : idx for idx, channel in enumerate(channels)}
    
    def channel_error(x, channel):
        ret = row[channel] - x[idx[channel]]
        for from_channel in [c for c in channels if c != channel]:
            ret -= splines[from_channel][channel](x[idx[from_channel]])
        return ret
    
    def row_error(x):
        ret = [channel_error(x, channel) for channel in channels]
        return ret
    
    x_0 = pandas.to_numeric(row.loc[channels])
    x = scipy.optimize.root(row_error, x_0)
    
    ret = row.copy()
    for idx, channel in enumerate(channels):
        ret[channel] = x.x[idx]
        
    return ret
        
@provides(cytoflow.views.IView)
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
        
        if not experiment:
            raise util.CytoflowOpError("No experiment specified")
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
         
        plt.figure()
        
        channels = self.op._splines.keys()
        num_channels = len(channels)
        
        for from_idx, from_channel in enumerate(channels):
            for to_idx, to_channel in enumerate(channels):
                if from_idx == to_idx:
                    continue
                
                tube_data = parse_tube(self.op.controls[from_channel], experiment)

                plt.subplot(num_channels, 
                            num_channels, 
                            from_idx + (to_idx * num_channels) + 1)
                plt.xscale('log', nonposx='mask')
                plt.yscale('log', nonposy='mask')
                plt.xlabel(from_channel)
                plt.ylabel(to_channel)
                plt.scatter(tube_data[from_channel],
                            tube_data[to_channel],
                            alpha = 0.1,
                            s = 1,
                            marker = 'o')
                
                spline = self.op._splines[from_channel][to_channel]
                xs = np.logspace(-1, math.log(tube_data[from_channel].max(), 10))
            
                plt.plot(xs, 
                         spline(xs), 
                         'g-', 
                         lw=3)
        
        plt.tight_layout(pad = 0.8)

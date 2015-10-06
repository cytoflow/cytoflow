'''
Created on Aug 26, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Python, \
                       Instance, Int, List, provides
import numpy as np
import math
import scipy.interpolate
import scipy.optimize
import pandas
import fcsparser

from cytoflow.operations.i_operation import IOperation
from cytoflow.operations.hlog import hlog, hlog_inv
from cytoflow.views import IView
from cytoflow.utility import CytoflowOpError, cartesian

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
    >>> bl_op.default_view().plot()    
    >>>
    >>> %time ex3 = bl_op.apply(ex2) # 410,000 cells
    CPU times: user 577 ms, sys: 27.7 ms, total: 605 ms
    Wall time: 607 ms
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.bleedthrough_piecewise"
    friendly_id = "Piecewise Bleedthrough Correction"
    
    name = CStr()

    controls = Dict(Str, File)
    num_knots = Int(7)
    mesh_size = Int(32)

    _splines = Dict(Str, Dict(Str, Python))
    _interpolators = Dict(Str, Python)
    
    # because the order of the channels is important, we can't just call
    # _interpolators.keys()
    _channels = List(Str)
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the bleedthrough from the single-channel controls in `controls`
        """

        if self.num_knots < 3:
            raise CytoflowOpError("Need to allow at least 3 knots in the spline")
        
        self._channels = self.controls.keys()
    
        for channel in self._channels:
            try:
                tube_meta = fcsparser.parse(self.controls[channel], 
                                            meta_data_only = True, 
                                            reformat_meta = True)
                tube_channels = tube_meta["_channels_"].set_index("$PnN")
            except Exception as e:
                raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(self.controls[channel], e.value))

            for channel in self._channels:
                exp_v = experiment.metadata[channel]['voltage']
            
                if not "$PnV" in tube_channels.ix[channel]:
                    raise CytoflowOpError("Didn't find a voltage for channel {0}" 
                                          "in tube {1}".format(channel, self.controls[channel]))
                
                control_v = tube_channels.ix[channel]["$PnV"]
                
                if control_v != exp_v:
                    raise CytoflowOpError("Voltage differs for channel {0} in tube {1}"
                                          .format(channel, self.controls[channel]))

        self._splines = {}
        mesh_axes = []

        for channel in self._channels:
            self._splines[channel] = {}

            try:
                tube_meta, tube_data = fcsparser.parse(self.controls[channel], 
                                                       reformat_meta = True)
                tube_channels = tube_meta["_channels_"].set_index("$PnN")
            except Exception as e:
                raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(self.controls[channel], e.value))
            
            data = tube_data.sort(channel)

            for af_channel in self._channels:
                if 'af_median' in experiment.metadata[af_channel]:
                    data[af_channel] = data[af_channel] - \
                                    experiment.metadata[af_channel]['af_median']

            channel_min = data[channel].min()
            channel_max = data[channel].max()
            
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
            mesh_min = -3 * experiment.metadata[channel]['af_stdev']
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
                    scipy.interpolate.LSQUnivariateSpline(data[from_channel].values,
                                                          data[to_channel].values,
                                                          t = knots,
                                                          k = 1)
         
        
        mesh = pandas.DataFrame(cartesian(mesh_axes), 
                                columns = [x for x in self._channels])
         
        mesh_corrected = mesh.apply(_correct_bleedthrough,
                                    axis = 1,
                                    args = ([[x for x in self._channels], 
                                             self._splines]))
        
        for channel in self._channels:
            chan_values = np.reshape(mesh_corrected[channel], [len(x) for x in mesh_axes])
            self._interpolators[channel] = \
                scipy.interpolate.RegularGridInterpolator(mesh_axes, chan_values)

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
                
        if not self._interpolators:
            raise CytoflowOpError("Module interpolators aren't set. "
                                  "Did you run estimate()?")
        
        if not set(self._interpolators.keys()) <= set(experiment.channels):
            raise CytoflowOpError("Module parameters don't match experiment channels")

        new_experiment = experiment.clone()
        
        # get rid of data outside of the interpolators' mesh 
        # (-3 * autofluorescence sigma)
        for channel in self._channels:
            af_stdev = new_experiment.metadata[channel]['af_stdev']
            new_experiment.data = \
                new_experiment.data[new_experiment.data[channel] > -3 * af_stdev]
        
        new_experiment.data.reset_index(drop = True, inplace = True)
        
        old_data = new_experiment.data[self._channels]
        
        for channel in self._channels:
            new_experiment[channel] = self._interpolators[channel](old_data)
            
            # add the correction splines to the experiment metadata so we can 
            # correct other controls later on
            new_experiment.metadata[channel]['piecewise_bleedthrough'] = \
                (self._channels, self._interpolators[channel])

        return new_experiment
    
    def default_view(self):
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """
        
        if set(self.controls.keys()) != set(self._splines.keys()):
            raise CytoflowOpError("Must have both the controls and bleedthrough to plot")
 
        channels = self.controls.keys()
        
        # make sure we can get the control tubes to plot the diagnostic
        for channel in channels:       
            try:
                _ = fcsparser.parse(self.controls[channel], 
                                    meta_data_only = True, 
                                    reformat_meta = True)
            except Exception as e:
                raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(self.controls[channel], e.value))

        return BleedthroughPiecewiseDiagnostic(op = self)
    
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
    
    x_0 = row.loc[channels].convert_objects(convert_numeric = True)
    x = scipy.optimize.root(row_error, x_0)
    
    ret = row.copy()
    for idx, channel in enumerate(channels):
        ret[channel] = x.x[idx]
        
    return ret
        
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
        
        channels = self.op._splines.keys()
        num_channels = len(channels)
        
        for from_idx, from_channel in enumerate(channels):
            for to_idx, to_channel in enumerate(channels):
                if from_idx == to_idx:
                    continue
                
                try:
                    _, tube_data = fcsparser.parse(self.op.controls[from_channel], 
                                                   reformat_meta = True)
                except Exception as e:
                    raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                          .format(self.op.controls[from_channel], e.value))
             
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

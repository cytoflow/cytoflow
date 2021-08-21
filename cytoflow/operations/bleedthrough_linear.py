#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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

"""
cytoflow.operations.bleedthrough_linear
---------------------------------------

The `bleedthrough_linear` module contains two classes:

`BleedthroughLinearOp` -- compensates for spectral bleedthrough
in a `Experiment` using single-color controls

`BleedthroughLinearDiagnostic` -- a diagnostic view to make sure
that `BleedthroughLinearOp` correctly estimated its parameters.
"""

import os, math
from natsort import natsorted

from traits.api import (HasStrictTraits, Str, File, Dict, Instance,
                        Constant, Tuple, Float, Any, provides)
    
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.optimize

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
    call `estimate` to parameterize the operation; check that the bleedthrough 
    plots look good by calling `BleedthroughLinearDiagnostic.plot` on 
    the `BleedthroughLinearDiagnostic` instance returned by 
    `default_view`; and then `apply` on an `Experiment`.
    
    Attributes
    ----------
    controls : Dict(Str, File)
        The channel names to correct, and corresponding single-color control
        FCS files to estimate the correction splines with.  Must be set to
        use `estimate`.
        
    spillover : Dict(Tuple(Str, Str), Float)
        The spillover "matrix" to use to correct the data.  The keys are pairs
        of channels, and the values are proportions of spectral overlap.  If 
        ``("channel1", "channel2")`` is present as a key, 
        ``("channel2", "channel1")`` must also be present.  The module does not
        assume that the matrix is symmetric.
        
    control_conditions : Dict(Str, Dict(Str, Any))
        Occasionally, you'll need to specify the experimental conditions that
        the bleedthrough tubes were collected under (to apply the operations in the 
        history.)  Specify them here.  The key is the channel name; they value
        is a dictionary of the conditions (same as you would specify for a
        `Tube` )

    Examples
    --------

    Create a small experiment:
    
    .. plot::
        :context: close-figs
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
        >>> ex = import_op.apply()

    Correct for autofluorescence
    
    .. plot::
        :context: close-figs
        
        >>> af_op = flow.AutofluorescenceOp()
        >>> af_op.channels = ["Pacific Blue-A", "FITC-A", "PE-Tx-Red-YG-A"]
        >>> af_op.blank_file = "tasbe/blank.fcs"
        
        >>> af_op.estimate(ex)
        >>> af_op.default_view().plot(ex)  

        >>> ex2 = af_op.apply(ex) 
    
    Create and parameterize the operation
    
    .. plot::
        :context: close-figs
        
        >>> bl_op = flow.BleedthroughLinearOp()
        >>> bl_op.controls = {'Pacific Blue-A' : 'tasbe/ebfp.fcs',
        ...                   'FITC-A' : 'tasbe/eyfp.fcs',
        ...                   'PE-Tx-Red-YG-A' : 'tasbe/mkate.fcs'}
    
    Estimate the model parameters
    
    .. plot::
        :context: close-figs 
    
        >>> bl_op.estimate(ex2)
    
    Plot the diagnostic plot
    
    .. note::
       The diagnostic plots look really bad in the online documentation.
       They're better in a real-world example, I promise!
    
    .. plot::
        :context: close-figs

        >>> bl_op.default_view().plot(ex2)  

    Apply the operation to the experiment
    
    .. plot::
        :context: close-figs
    
        >>> ex2 = bl_op.apply(ex2)  
    
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.bleedthrough_linear')
    friendly_id = Constant("Linear Bleedthrough Correction")
    
    name = Constant("Bleedthrough")

    controls = Dict(Str, File)
    spillover = Dict(Tuple(Str, Str), Float)
    control_conditions = Dict(Str, Dict(Str, Any), {})
    
    _sample = Dict(Str, Any, transient = True)
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the bleedthrough from simgle-channel controls in `controls`
        """
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        channels = list(self.controls.keys())

        if len(channels) < 2:
            raise util.CytoflowOpError('channels',
                                       "Need at least two channels to correct bleedthrough.")

        # make sure the control files exist
        for channel in channels:
            if not os.path.isfile(self.controls[channel]):
                raise util.CytoflowOpError('channels',
                                           "Can't find file {0} for channel {1}."
                                           .format(self.controls[channel], channel))
                
        self.spillover = {}
        self._sample.clear()
                
        spillover = {}
        for channel in channels:
            
            # make a little Experiment
            check_tube(self.controls[channel], experiment)
            tube_conditions = self.control_conditions[channel] if channel in self.control_conditions else {}
            exp_conditions = {k: experiment.data[k].dtype.name for k in tube_conditions.keys()}

            tube_exp = ImportOp(tubes = [Tube(file = self.controls[channel],
                                              conditions = tube_conditions)],
                                conditions = exp_conditions,
                                channels = {experiment.metadata[c]["fcs_name"] : c for c in experiment.channels},
                                name_metadata = experiment.metadata['name_metadata']).apply()
            
            # apply previous operations
            for op in experiment.history:
                if hasattr(op, 'by'):
                    for by in op.by:
                        if 'experiment' in experiment.metadata[by]:
                            raise util.CytoflowOpError('experiment',
                                                       "Prior to applying this operation, "
                                                       "you must not apply any operation with 'by' "
                                                       "set to an experimental condition.")
                tube_exp = op.apply(tube_exp)
                
            # subset it
            if subset:
                try:
                    tube_exp = tube_exp.query(subset)
                except Exception as exc:
                    raise util.CytoflowOpError('subset',
                                               "Subset string '{0}' isn't valid"
                                               .format(self.subset)) from exc
                                
                if len(tube_exp.data) == 0:
                    raise util.CytoflowOpError('subset',
                                               "Subset string '{0}' returned no events"
                                               .format(self.subset))
            
            tube_data = tube_exp.data
                
            # polyfit requires sorted data
            tube_data.sort_values(channel, inplace = True)
            
            # save a little of the data to plot later
            self._sample[channel] = tube_data.sample(n = 1000)

            from_channel = channel
            
            # sometimes some of the data is off the edge of the
            # plot, and this screws up a linear regression
            
            from_min = np.min(tube_data[from_channel]) * 1.025
            from_max = np.max(tube_data[from_channel]) * 0.975
            tube_data[from_channel] = \
                tube_data[from_channel].clip(from_min, from_max)
            for to_channel in channels:
                
                if from_channel == to_channel:
                    continue
                
                to_min = np.min(tube_data[to_channel]) * 1.025
                to_max = np.max(tube_data[to_channel]) * 0.975
                tube_data[to_channel] = \
                    tube_data[to_channel].clip(to_min, to_max)
                
                tube_data.reset_index(drop = True, inplace = True)
                 
                f = lambda x, k: x * k
                 
                popt, _ = scipy.optimize.curve_fit(f,
                                                   tube_data[from_channel],
                                                   tube_data[to_channel],
                                                   0)
                 
                spillover[(from_channel, to_channel)] = popt[0]
                
        # set this atomically - to support GUI
        self.spillover = spillover
                
    def apply(self, experiment):
        """
        Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : `Experiment`
            The experiment to which this operation is applied
            
        Returns
        -------
        Experiment
            A new `Experiment` with the bleedthrough subtracted out.  
            The corrected channels have the following metadata added:
            
            - **linear_bleedthrough** : Dict(Str : Float)
              The values for spillover from other channels into this channel.
        
            - **bleedthrough_channels** : List(Str)
              The channels that were used to correct this one.
        
            - **bleedthrough_fn** : Callable (Tuple(Float) --> Float)
              The function that will correct one event in this channel.  Pass it
              the values specified in `bleedthrough_channels` and it will return
              the corrected value for this channel.
        """
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        if not self.spillover:
            raise util.CytoflowOpError('spillover',
                                       "Spillover matrix isn't set. "
                                       "Did you forget to run estimate()?")
        
        for (from_channel, to_channel) in self.spillover:
            if not from_channel in experiment.data:
                raise util.CytoflowOpError('spillover',
                                           "Can't find channel {0} in experiment"
                                           .format(from_channel))
            if not to_channel in experiment.data:
                raise util.CytoflowOpError('spillover',
                                           "Can't find channel {0} in experiment"
                                           .format(to_channel))
                
            if not (to_channel, from_channel) in self.spillover:
                raise util.CytoflowOpError('spillover',
                                           "Must have both (from, to) and "
                                           "(to, from) keys in self.spillover")
        
        new_experiment = experiment.clone(deep = True)
        
        # the completely arbitrary ordering of the channels
        channels = list(set([x for (x, _) in list(self.spillover.keys())]))
         
        # build the spillover matrix from the spillover dictionary
        a = [  [self.spillover[(y, x)] if x != y else 1.0 for x in channels]
               for y in channels]
         
        # invert it.  use the pseudoinverse in case a is singular
        a_inv = np.linalg.pinv(a)
         
        # compute the corrected channels
        new_channels = np.dot(experiment.data[channels], a_inv)
         
        # and assign to the new experiment
        for i, c in enumerate(channels):
            new_experiment[c] = pd.Series(new_channels[:, i])
            
        # make sure the new experiment has the same column order as the old one
        new_experiment.data = new_experiment.data[list(experiment.data.columns)]
         
        for channel in channels:
            # add the spillover values to the channel's metadata
            new_experiment.metadata[channel]['linear_bleedthrough'] = \
                {x : self.spillover[(x, channel)]
                     for x in channels if x != channel}
            new_experiment.metadata[channel]['bleedthrough_channels'] = list(channels)
            new_experiment.metadata[channel]['bleedthrough_fn'] = lambda x, a_inv = a_inv: np.dot(x, a_inv)
      
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))   
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to make sure spillover estimation is working.
        
        Returns
        -------
        `IView`
            An `IView`, call `BleedthroughLinearDiagnostic.plot` to see the diagnostic plots
        """
 
        # the completely arbitrary ordering of the channels
        channels = list(set([x for (x, _) in list(self.spillover.keys())]))
        
        if set(self.controls.keys()) != set(channels):
            raise util.CytoflowOpError('controls',
                                       "Must have both the controls and bleedthrough to plot")

        v = BleedthroughLinearDiagnostic(op = self)
        v.trait_set(**kwargs)
        return v
    
@provides(cytoflow.views.IView)
class BleedthroughLinearDiagnostic(HasStrictTraits):
    """
    Plots a scatterplot of each channel vs every other channel and the 
    bleedthrough line
    
    Attributes
    ----------
    op : Instance(BleedthroughPiecewiseOp)
        The operation whose parameters we're viewing.  If you made the instance
        with `BleedthroughPLinearOp.default_view`, this is set for you
        already.
        
    subset : str
        If set, only plot this subset of the underlying data.
        
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.linearbleedthroughdiagnostic")
    friendly_id = Constant("Linear Bleedthrough Diagnostic") 
    
    subset = Str
    
    # TODO - why can't I use BleedthroughPiecewiseOp here?
    op = Instance(IOperation)
    
    def plot(self, experiment = None, **kwargs):
        """
        Plot a diagnostic of the bleedthrough model computation.
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")

        if not self.op.controls:
            raise util.CytoflowViewError('op',
                                         "No controls specified")
        
        if not self.op.spillover:
            raise util.CytoflowViewError('op',
                                         "No spillover matrix specified")
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
        
        channels = natsorted(list(set([x for (x, _) in list(self.op.spillover.keys())])))
        num_channels = len(channels)
        _, axes2d = plt.subplots(nrows=num_channels, ncols=num_channels)    
        
        # the completely arbitrary ordering of the channels
        # num_channels = len(channels)

        for to_idx, row in enumerate(axes2d):
            for from_idx, ax in enumerate(row):
                
                plt.sca(ax)
                
                from_channel = channels[from_idx]
                to_channel = channels[to_idx]
                
                if to_idx == len(axes2d) - 1 or (to_idx == len(axes2d) - 2 and from_idx == len(row) - 1):
                    plt.xlabel(from_channel)
                if from_idx == 0 or (from_idx == 1 and to_idx == 0):
                    plt.ylabel(to_channel)
        
                if from_idx == to_idx:
                    ax.set_visible(False)
                    continue
                
                tube_data = self.op._sample[from_channel]
                
                # for ReadTheDocs, which doesn't have swig
                import sys
                if 'cytoflow.utility.logicle_ext.Logicle' in sys.modules:
                    scale_name = 'logicle'
                else:
                    scale_name = 'log'
                
                xscale = util.scale_factory(scale_name, experiment, channel = from_channel)
                yscale = util.scale_factory(scale_name, experiment, channel = to_channel)

                plt.xscale(scale_name, **xscale.get_mpl_params(ax.get_xaxis()))
                plt.yscale(scale_name, **yscale.get_mpl_params(ax.get_yaxis()))

                plt.scatter(tube_data[from_channel],
                            tube_data[to_channel],
                            alpha = 1,
                            s = 1,
                            marker = 'o')
                
                xs = np.logspace(-1, math.log(tube_data[from_channel].max(), 10))
                ys = xs * self.op.spillover[(from_channel, to_channel)]
          
                plt.plot(xs, ys, 'g-', lw=3)

                
        plt.tight_layout(pad = 0.8)

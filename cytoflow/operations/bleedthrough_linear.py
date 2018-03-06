#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
cytoflow.operations.bleedthrough_linear
---------------------------------------
'''
import os, math

from traits.api import HasStrictTraits, Str, File, Dict, Instance, \
                       Constant, Tuple, Float, provides
    
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.optimize

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation
from .import_op import Tube, ImportOp, check_tube

from pandas import DataFrame
from ..experiment import Experiment

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
    
    To use, set up the :attr:`controls` dict with the single color controls;
    call :meth:`estimate` to parameterize the operation; check that the bleedthrough 
    plots look good by calling :meth:`~.BleedthroughLinearDiagnostic.plot` on 
    the :class:`BleedthroughLinearDiagnostic` instance returned by 
    :meth:`default_view`; and then :meth:`apply` on an :class:`.Experiment`.
    
    Attributes
    ----------
    controls : Dict(Str, File)
        The channel names to correct, and corresponding single-color control
        FCS files to estimate the correction splines with.  Must be set to
        use :meth:`estimate`.
        
    spillover : Dict(Tuple(Str, Str), Float)
        The spillover "matrix" to use to correct the data.  The keys are pairs
        of channels, and the values are proportions of spectral overlap.  If 
        ``("channel1", "channel2")`` is present as a key, 
        ``("channel2", "channel1")`` must also be present.  The module does not
        assume that the matrix is symmetric.

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
    controls_frames = Dict(Str, Instance(DataFrame))
    spillover = Dict(Tuple(Str, Str), Float)
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the bleedthrough from simgle-channel controls in :attr:`controls`
        """
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        if ( self.controls_frames != {} ):
            channels = list(self.controls_frames.keys())
        else:
            channels = list(self.controls.keys())
        

        if len(channels) < 2:
            raise util.CytoflowOpError('channels',
                                       "Need at least two channels to correct bleedthrough.")

        # make sure the control files exist
        if ( self.controls != {} ):
            for channel in channels:
                if not os.path.isfile(self.controls[channel]):
                    raise util.CytoflowOpError('channels',
                                               "Can't find file {0} for channel {1}."
                                               .format(self.controls[channel], channel))
                
        for channel in channels:
            ex_channels = {experiment.metadata[c]["fcs_name"] : c for c in experiment.channels}
            name_metadata = experiment.metadata['name_metadata']
            if ( self.controls != {} ):
                # make a little Experiment
                check_tube(self.controls[channel], experiment)
                tube_exp = ImportOp(tubes = [Tube(file = self.controls[channel])],
                                    channels = ex_channels,
                                    name_metadata = name_metadata).apply()
            else:
                tube_exp = ImportOp(tubes = [Tube(frame = self.controls_frames[channel])],
                                    channels = ex_channels,
                                    name_metadata = name_metadata).apply()

            # apply previous operations
            for op in experiment.history:
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
                 
                self.spillover[(from_channel, to_channel)] = popt[0]
                
    def apply(self, experiment):
        """Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            The experiment to which this operation is applied
            
        Returns
        -------
        Experiment
            A new :class:`Experiment` with the bleedthrough subtracted out.  
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
        
        new_experiment = experiment.clone()
        
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
        IView
            An IView, call :meth:`~BleedthroughLinearDiagnostic.plot` to see the diagnostic plots
        """
 
        # the completely arbitrary ordering of the channels
        channels = list(set([x for (x, _) in list(self.spillover.keys())]))
        
        if ( self.controls_frames != {} ):
            mykeys = self.controls_frames.keys()
        else:
            mykeys = self.controls.keys()

            if set(mykeys) != set(channels):
                raise util.CytoflowOpError('controls',
                                           "Must have both the controls and bleedthrough to plot")

        return BleedthroughLinearDiagnostic(op = self, **kwargs)
    
@provides(cytoflow.views.IView)
class BleedthroughLinearDiagnostic(HasStrictTraits):
    """
    Plots a scatterplot of each channel vs every other channel and the 
    bleedthrough line
    
    Attributes
    ----------
    op : Instance(BleedthroughPiecewiseOp)
        The operation whose parameters we're viewing.  If you made the instance
        with :meth:`BleedthroughPLinearOp.default_view`, this is set for you
        already.
        
    subset : str
        If set, only plot this subset of the underlying data.
        
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.autofluorescencediagnosticview")
    friendly_id = Constant("Autofluorescence Diagnostic") 
    
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

        if not self.op.controls and not self.op.controls_frames:
            raise util.CytoflowViewError('op',
                                         "No controls specified")
        
        if not self.op.spillover:
            raise util.CytoflowViewError('op',
                                         "No spillover matrix specified")
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
         
        plt.figure()
        
        # the completely arbitrary ordering of the channels
        channels = list(set([x for (x, _) in list(self.op.spillover.keys())]))
        num_channels = len(channels)
        
        for from_idx, from_channel in enumerate(channels):
            for to_idx, to_channel in enumerate(channels):
                if from_idx == to_idx:
                    continue
                
                ex_channels = {experiment.metadata[c]["fcs_name"] : c for c in experiment.channels}
                name_metadata = experiment.metadata['name_metadata']
                if ( self.op.controls != {} ):
                    # make a little Experiment
                    check_tube(self.op.controls[from_channel], experiment)
                    tube_exp = ImportOp(tubes = [Tube(file = self.op.controls[from_channel])],
                                        channels = ex_channels,
                                        name_metadata = name_metadata).apply()
                else:
                    tube_exp = ImportOp(tubes = [Tube(frame = self.op.controls_frames[from_channel])],
                                        channels = ex_channels,
                                        name_metadata = name_metadata).apply()
                
                # apply previous operations
                for op in experiment.history:
                    tube_exp = op.apply(tube_exp)
                    
                # subset it
                if self.subset:
                    try:
                        tube_exp = tube_exp.query(self.subset)
                    except Exception as e:
                        raise util.CytoflowViewError('subset',
                                                   "Subset string '{0}' isn't valid"
                                              .format(self.subset)) from e
                                    
                    if len(tube_exp.data) == 0:
                        raise util.CytoflowViewError('subset',
                                                   "Subset string '{0}' returned no events"
                                              .format(self.subset))
                    
                tube_data = tube_exp.data
                
                # for ReadTheDocs, which doesn't have swig
                import sys
                if sys.modules['cytoflow.utility.logicle_ext.Logicle'].__name__ != 'cytoflow.utility.logicle_ext.Logicle':
                    scale_name = 'log'
                else:
                    scale_name = 'logicle'
                
                xscale = util.scale_factory(scale_name, tube_exp, channel = from_channel)
                yscale = util.scale_factory(scale_name, tube_exp, channel = to_channel)

                plt.subplot(num_channels, 
                            num_channels, 
                            from_idx + (to_idx * num_channels) + 1)
                plt.xscale(scale_name, **xscale.mpl_params)
                plt.yscale(scale_name, **yscale.mpl_params)
                plt.xlabel(from_channel)
                plt.ylabel(to_channel)
                plt.scatter(tube_data[from_channel],
                            tube_data[to_channel],
                            alpha = 0.1,
                            s = 1,
                            marker = 'o')
                
                xs = np.logspace(-1, math.log(tube_data[from_channel].max(), 10))
                ys = xs * self.op.spillover[(from_channel, to_channel)]
          
                plt.plot(xs, ys, 'g-', lw=3)
                
        plt.tight_layout(pad = 0.8)

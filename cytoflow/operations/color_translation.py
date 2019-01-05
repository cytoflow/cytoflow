#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
cytoflow.operations.color_translation
-------------------------------------
'''
import math

from traits.api import (HasStrictTraits, Str, File, Dict, Any, Callable,
                        Instance, Tuple, Bool, Constant, provides, Float)
import numpy as np
import matplotlib.pyplot as plt
import sklearn.mixture
import scipy.optimize

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation
from .import_op import Tube, ImportOp, check_tube

@provides(IOperation)
class ColorTranslationOp(HasStrictTraits):
    """
    Translate measurements from one color's scale to another, using a two-color
    or three-color control.
    
    To use, set up the :attr:`controls` dictionary with the channels to convert
    and the FCS files to compute the mapping.  Call :meth:`estimate` to
    paramterize the module; check that the plots look good by calling the 
    :meth:`~ColorTranslationDiagnostic.plot` method of the 
    :class:`ColorTranslationDiagnostic` instance returned by :meth:`default_view`;
    then call :meth:`apply` to apply the translation to an :class:`.Experiment`.
    
    Attributes
    ----------
    controls : Dict((Str, Str), File)
        Two-color controls used to determine the mapping.  They keys are 
        tuples of **from-channel** and **to-channel**.  The values are FCS files 
        containing two-color constitutive fluorescent expression data 
        for the mapping.
        
    mixture_model : Bool (default = False)
        If ``True``, try to model the **from** channel as a mixture of expressing
        cells and non-expressing cells (as you would get with a transient
        transfection), then weight the regression by the probability that the
        the cell is from the top (transfected) distribution.  Make sure you 
        check the diagnostic plots to see that this worked!
        
    linear_model : Bool (default = False)
        Set this to ``True`` to get a scaling that is strictly multiplicative,
        mirroring the TASBE approach.  Do check the diagnostic plot, though,
        to see how well (or poorly) your model fits the data.
        
    control_conditions : Dict((Str, Str), Dict(Str, Any))
        Occasionally, you'll need to specify the experimental conditions that
        the bleedthrough tubes were collected under (to apply the operations in the 
        history.)  Specify them here.  The key is a tuple of channel names; the 
        value is a dictionary of the conditions (same as you would specify for a
        :class:`~.Tube` )

        
    Notes
    -----
    In the TASBE workflow, this operation happens *after* the application of
    :class:`.AutofluorescenceOp` and :class:`.BleedthroughLinearOp`.  The entire
    operation history of the :class:`.Experiment` that is passed to 
    :meth:`estimate` is replayed on the control files in :attr:`controls`, so
    they are also corrected for autofluorescence and bleedthrough, and have
    metadata for subsetting.
    

    Examples
    --------
    Create a small experiment:
    
    .. plot::
        :context: close-figs
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "tasbe/mkate.fcs")]
        >>> ex = import_op.apply()
    
    Create and parameterize the operation
    
    .. plot::
        :context: close-figs

        >>> color_op = flow.ColorTranslationOp()
        >>> color_op.controls = {("Pacific Blue-A", "FITC-A") : "tasbe/rby.fcs",
        ...                      ("PE-Tx-Red-YG-A", "FITC-A") : "tasbe/rby.fcs"}
        >>> color_op.mixture_model = True
    
    Estimate the model parameters
    
    .. plot::
        :context: close-figs 
    
        >>> color_op.estimate(ex)
    
    Plot the diagnostic plot
    
    .. plot::
        :context: close-figs

        >>> color_op.default_view().plot(ex)  

    Apply the operation to the experiment
    
    .. plot::
        :context: close-figs
    
        >>> ex = color_op.apply(ex)  
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.color_translation')
    friendly_id = Constant("Color translation")
    
    name = Constant("Color Translation")

    translation = util.Removed(err_string = "'translation' is removed; the same info is found in 'controls'", warning = True)
    controls = Dict(Tuple(Str, Str), File)
    mixture_model = Bool(False)
    linear_model = Bool(False)
    
    control_conditions = Dict(Tuple(Str, Str), Dict(Str, Any), {})

    # The regression coefficients determined by `estimate()`, used to map 
    # colors between channels.  The keys are tuples of (*from-channel*,
    # *to-channel) (corresponding to key-value pairs in `translation`).  The
    # values are lists of Float, the log-log coefficients for the color 
    # translation (determined by `estimate()`). 
    # TODO - why can't i make the value List(Float)?
    _coefficients = Dict(Tuple(Str, Str), Any, transient = True)
    _trans_fn = Dict(Tuple(Str, Str), Callable, transient = True)
    _sample = Dict(Tuple(Str, Str), Any, transient = True)
    _means = Dict(Tuple(Str, Str), Tuple(Float, Float), transient = True)

    def estimate(self, experiment, subset = None): 
        """
        Estimate the mapping from the two-channel controls
        
        Parameters
        ----------
        experiment : Experiment
            The :class:`.Experiment` used to check the voltages, etc. of the
            control tubes.  Also the source of the operation history that
            is replayed on the control tubes.
            
        subset : Str
            A Python expression used to subset the controls before estimating
            the color translation parameters.
        """

        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        if not self.controls:
            raise util.CytoflowOpError('controls',
                                       "No controls specified")
            
        self._coefficients.clear()
        self._trans_fn.clear()
        self._sample.clear()
        self._means.clear()

        tubes = {}
        
        translation = {x[0] : x[1] for x in list(self.controls.keys())}
        
        for from_channel, to_channel in translation.items():
            
            if from_channel not in experiment.channels:
                raise util.CytoflowOpError('translatin',
                                           "Channel {0} not in the experiment"
                                           .format(from_channel))
                
            if to_channel not in experiment.channels:
                raise util.CytoflowOpError('translation',
                                           "Channel {0} not in the experiment"
                                           .format(to_channel))
            
            if (from_channel, to_channel) not in self.controls:
                raise util.CytoflowOpError('translation',
                                           "Control file for {0} --> {1} "
                                           "not specified"
                                           .format(from_channel, to_channel))
                
            tube_file = self.controls[(from_channel, to_channel)]
            tube_conditions = self.control_conditions[(from_channel, to_channel)] \
                                    if (from_channel, to_channel) in self.control_conditions \
                                    else {}
            conditions = {k: experiment.data[k].dtype.name for k in tube_conditions.keys()}
            
            if tube_file not in tubes: 
                # make a little Experiment
                check_tube(tube_file, experiment)

                tube_exp = ImportOp(tubes = [Tube(file = tube_file,
                                                  conditions = tube_conditions)],
                                    conditions = conditions,
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

                # subset the events
                if subset:
                    try:
                        tube_exp = tube_exp.query(subset)
                    except Exception as e:
                        raise util.CytoflowOpError('subset',
                                                   "Subset string '{0}' isn't valid"
                                              .format(subset)) from e
                                    
                    if len(tube_exp.data) == 0:
                        raise util.CytoflowOpError('subset',
                                                   "Subset string '{0}' returned no events"
                                              .format(subset))
                
                tube_data = tube_exp.data    

                tubes[tube_file] = tube_data

                
            data = tubes[tube_file][[from_channel, to_channel]].copy()
            data = data[data[from_channel] > 0]
            data = data[data[to_channel] > 0]
            
            _ = data.reset_index(drop = True, inplace = True)
            
            self._sample[(from_channel, to_channel)] = data.sample(n = min(len(data), 5000))
            
            data[from_channel] = np.log10(data[from_channel])
            data[to_channel] = np.log10(data[to_channel])
            
            if self.mixture_model:    
                gmm = sklearn.mixture.BayesianGaussianMixture(n_components=2,
                                                              random_state = 1)
                fit = gmm.fit(data)
                
                self._means[(from_channel), (to_channel)] = \
                    (10 ** fit.means_[0][0], 10 ** fit.means_[1][0])

                # pick the component with the maximum mean
                idx = 0 if fit.means_[0][0] > fit.means_[1][0] else 1
                weights = [x[idx] for x in fit.predict_proba(data)]
            else:
                weights = [1] * len(data.index)
                
            if self.linear_model:
                # this mimics the TASBE approach, which constrains the fit to
                # a multiplicative scaling (eg, a linear fit with an intercept
                # of 0.)  I disagree that this is the right approach, which is
                # why it's not the default.
                 
                f = lambda x: weights * (data[to_channel] - x[0] * data[from_channel])
                x0 = [1]
                
                trans_fn = lambda data, x: np.power(data, x[0])
                 
            else:

                # this code uses a different approach from TASBE. instead of
                # computing a multiplicative scaling constant, it computes a
                # full linear regression on the log-scaled data (ie, allowing
                # the intercept to vary as well as the slope).  this is a 
                # more general model of the underlying physical behavior, and
                # fits the data better -- but it may not be more "correct."
                 
                f = lambda x: weights * (data[to_channel] - x[0] * data[from_channel] - x[1])
                x0 = [1, 0]
                
                trans_fn = lambda data, x: (10 ** x[1]) * np.power(data, x[0])
                 
                 
            opt = scipy.optimize.least_squares(f, x0)
            self._coefficients[(from_channel, to_channel)] = opt.x
            self._trans_fn[(from_channel, to_channel)] = lambda data, x = opt.x: trans_fn(data, x)


    def apply(self, experiment):
        """Applies the color translation to an experiment
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
        Experiment 
            a new experiment with the color translation applied.  The corrected
            channels also have the following new metadata:
    
            **channel_translation** : Str
            Which channel was this one translated to?
        
            **channel_translation_fn** : Callable (pandas.Series --> pandas.Series)
            The function that translated this channel
        """

        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        if not self.controls:
            raise util.CytoflowOpError('controls', "No controls specified")
        
        if not self._trans_fn:
            raise util.CytoflowOpError(None, "Transfer functions aren't set. "
                                       "Did you forget to call estimate()?")
            
        translation = {x[0] : x[1] for x in list(self.controls.keys())}
        from_channels = [x[0] for x in list(self.controls.keys())]

        for key, val in translation.items():
            if (key, val) not in self._coefficients:
                raise util.CytoflowOpError(None,
                                           "Coefficients aren't set for translation "
                                           "{} --> {}.  Did you call estimate()?"
                                           .format(key, val))
                       
        new_experiment = experiment.clone()
        
        for channel in from_channels:
            new_experiment.data = \
                new_experiment.data[new_experiment.data[channel] > 0]
        
        for from_channel, to_channel in translation.items():
            trans_fn = self._trans_fn[(from_channel, to_channel)]
                        
            new_experiment[from_channel] = trans_fn(experiment[from_channel])
            new_experiment.metadata[from_channel]['channel_translation_fn'] = trans_fn
            new_experiment.metadata[from_channel]['channel_translation'] = to_channel
            
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
            
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
        IView
            A diagnostic view, call :meth:`ColorTranslationDiagnostic.plot` to 
            see the diagnostic plots
        """

        v = ColorTranslationDiagnostic(op = self)
        v.trait_set(**kwargs)
        return v
    
@provides(cytoflow.views.IView)
class ColorTranslationDiagnostic(HasStrictTraits):
    """
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
    
    op : Instance(ColorTranslationOp)
        The op whose parameters we're viewing
        
    subset : str
        A Python expression specifying a subset of the events in the control 
        FCS files to plot
    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.colortranslationdiagnostic")
    friendly_id = Constant("Color Translation Diagnostic")
    
    subset = Str
    
    # TODO - why can't I use ColorTranslationOp here?
    op = Instance(IOperation)
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots
        
        Parameters
        ----------
        experiment : Experiment
            
        """
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
        
        if not self.op.controls:
            raise util.CytoflowViewError('op',
                                         "No controls specified")
        
        if not self.op._trans_fn:
            raise util.CytoflowViewError('op',
                                         "Transfer functions aren't set. "
                                         "Did you forget to call estimate()?")
        
        translation = {x[0] : x[1] for x in list(self.op.controls.keys())}
        
        plt.figure()
        num_plots = len(list(self.op.controls.keys()))
        plt_idx = 0
        
        for from_channel, to_channel in translation.items():
#                     
#             from_range = experiment.metadata[from_channel]['range']
#             to_range = experiment.metadata[to_channel]['range']
            data = self.op._sample[(from_channel, to_channel)]
            from_min = data[from_channel].quantile(0.01)
            from_max = data[from_channel].quantile(0.99)
            to_min = data[to_channel].quantile(0.01)
            to_max = data[to_channel].quantile(0.99)

            if self.op.mixture_model:    
                plt.subplot(num_plots, 2, plt_idx * 2 + 2)
                plt.xscale('log', nonposx='mask')
                hist_bins = np.logspace(1, math.log(data[from_channel].max(), 2), num = 128, base = 2)
                _ = plt.hist(data[from_channel],
                             bins = hist_bins,
                             histtype = 'stepfilled',
                             linewidth = 0,
                             antialiased = True)
                plt.xlabel(from_channel)
                    
                plt.axvline(self.op._means[(from_channel, to_channel)][0], color = 'r')
                plt.axvline(self.op._means[(from_channel, to_channel)][1], color = 'r')

            
            num_cols = 2 if self.op.mixture_model else 1
            plt.subplot(num_plots, num_cols, plt_idx * num_cols + 1)
            plt.xscale('log', nonposx = 'mask')
            plt.yscale('log', nonposy = 'mask')
            plt.xlabel(from_channel)
            plt.ylabel(to_channel)
            plt.xlim(from_min, from_max)
            plt.ylim(to_min, to_max)
            
            kwargs.setdefault('alpha', 0.2)
            kwargs.setdefault('s', 1)
            kwargs.setdefault('marker', 'o')
            
            plt.scatter(data[from_channel],
                        data[to_channel],
                        **kwargs)          

            xs = np.logspace(1, math.log(data[from_channel].max(), 2), num = 256, base = 2)
            trans_fn = self.op._trans_fn[(from_channel, to_channel)]
            plt.plot(xs, trans_fn(xs), "--r")
            
            
            plt_idx = plt_idx + 1
        
        plt.tight_layout(pad = 0.8)

'''
Created on Sep 2, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Python, \
                       Instance, Tuple, Bool, Constant, provides
import numpy as np
import fcsparser
import warnings
import matplotlib.pyplot as plt
import math
import sklearn.mixture

from cytoflow.operations import IOperation
from cytoflow.views import IView
from cytoflow.utility import CytoflowOpError, CytoflowViewError

@provides(IOperation)
class ColorTranslationOp(HasStrictTraits):
    """
    Translate measurements from one color's scale to another, using a two-color
    or three-color control.
    
    To use, set up the `channels` dict with the desired mapping and the 
    `controls` dict with the multi-color controls.  Call `estimate()` to
    paramterize the module; check that the plots look good with 
    `default_view().plot()`; then `apply()` to an Experiment.
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation; optional for interactive use)
        
    translation : Dict(Str, Str)
        Specifies the desired translation.  The keys are the channel names
        to map *from*; the values are the channel names to map *to*.
        
    controls : Dict((Str, Str), File)
        Two-color controls used to determine the mapping.  They keys are 
        tuples of *from-channel* and *to-channel* (corresponding to key-value
        pairs in `translation`).  The values are FCS files containing two-color 
        constitutive fluorescent expression for the mapping.
        
    mixture_model : Bool (default = False)
        If "True", try to model the "from" channel as a mixture of expressing
        cells and non-expressing cells (as you would get with a transient
        transfection.)  Make sure you check the diagnostic plots!
        
    Notes
    -----
    In the TASBE workflow, this operation happens *after* the application of
    `AutofluorescenceOp` and `BleedthroughPiecewiseOp`.  Both must be applied
    to the single-color controls before the translation coefficients are
    estimated; the autofluorescence and bleedthrough parameters for each channel 
    are retrieved from the channel metadata and applied in `estimate()`.
    
    However, because there are possible workflows for which the autofluorescence
    and bleedthrough corrections are not necessary, `estimate()` does NOT fail
    if those parameters are not available; it simply does not apply the
    corresponding corrections.

    Examples
    --------
    >>> ct_op = flow.ColorTranslationOp()
    >>> ct_op.translation = {"Pacific Blue-A" : "FITC-A",
    ...                      "PE-Tx-Red-YG-A" : "FITC-A"}
    >>> ct_op.controls = {("Pacific Blue-A", "FITC-A") : "merged/rby.fcs",
    ...                   ("PE-Tx-Red-YG-A", "FITC-A") : "merged/rby.fcs"}
    >>> ct_op.mixture_model = True
    >>>
    >>> ct_op.estimate(ex4)
    >>> ct_op.default_view().plot(ex4)
    >>> ex5 = ct_op.apply(ex4)
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.color_translation')
    friendly_id = Constant("Color translation")
    
    name = CStr()

    translation = Dict(Str, Str)
    controls = Dict(Tuple(Str, Str), File, transient = True)
    mixture_model = Bool(False, transient = True)

    # The regression coefficients determined by `estimate()`, used to map 
    # colors between channels.  The keys are tuples of (*from-channel*,
    # *to-channel) (corresponding to key-value pairs in `translation`).  The
    # values are lists of Float, the log-log coefficients for the color 
    # translation (determined by `estimate()`). 
    # TODO - why can't i make the value List(Float)?
    _coefficients = Dict(Tuple(Str, Str), Python)

    def estimate(self, experiment, subset = None): 
        """
        Estimate the mapping from the two-channel controls
        """

        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        exp_channels = [x for x in experiment.metadata 
                        if 'type' in experiment.metadata[x] 
                        and experiment.metadata[x]['type'] == "channel"]
        
        tubes = {}

        for from_channel, to_channel in self.translation.iteritems():
            
            if from_channel not in exp_channels:
                raise CytoflowOpError("Channel {0} not in the experiment"
                                      .format(from_channel))
                
            if to_channel not in exp_channels:
                raise CytoflowOpError("Channel {0} not in the experiment"
                                      .format(to_channel))
            
            if (from_channel, to_channel) not in self.controls:
                raise CytoflowOpError("Control file for {0} --> {1} "
                                      "not specified"
                                      .format(from_channel, to_channel))
                
            tube_file = self.controls[(from_channel, to_channel)]
            
            if tube_file not in tubes: 
                try:
                    channel_naming = experiment.metadata["name_meta"]
                    tube_meta, tube_data = \
                        fcsparser.parse(tube_file, 
                                        reformat_meta = True,
                                        channel_naming = channel_naming)
                    tube_channels = tube_meta["_channels_"].set_index("$PnN")
                except Exception as e:
                    raise CytoflowOpError("FCS reader threw an error on tube "
                                          "{0}: {1}"
                                          .format(tube_file, str(e)))

                # check voltages
                for channel in [from_channel, to_channel]:
                    exp_v = experiment.metadata[channel]['voltage']
                
                    if not "$PnV" in tube_channels.ix[channel]:
                        raise CytoflowOpError("Didn't find a voltage for "
                                              "channel {0} in tube {1}"
                                              .format(channel, 
                                                      self.controls[channel]))
                    
                    control_v = tube_channels.ix[channel]["$PnV"]
                    
                    if control_v != exp_v:
                        raise CytoflowOpError("Voltage differs for channel "
                                              "{0} in tube {1}"
                                              .format(channel, 
                                                      self.controls[channel]))

                # autofluorescence correction
                af = [(channel, (experiment.metadata[channel]['af_median'],
                                 experiment.metadata[channel]['af_stdev'])) 
                      for channel in exp_channels
                      if 'af_median' in experiment.metadata[channel]]
                
                for af_channel, (af_median, af_stdev) in af:
                    tube_data[af_channel] = tube_data[af_channel] - af_median
                    tube_data = tube_data[tube_data[af_channel] > -3 * af_stdev]
                    
                tube_data.reset_index(drop = True, inplace = True)
                    
                # bleedthrough correction
                old_tube_data = tube_data.copy()
                bleedthrough = \
                    {channel: experiment.metadata[channel]['piecewise_bleedthrough']
                     for channel in exp_channels
                     if 'piecewise_bleedthrough' in experiment.metadata[channel]} 

                for channel, (interp_channels, interpolator) in bleedthrough.iteritems():
                    interp_data = old_tube_data[interp_channels]
                    tube_data[channel] = interpolator(interp_data)
        
                # bead calibration
                beads = [(channel, experiment.metadata[channel]['bead_calibration_fn'])
                         for channel in exp_channels
                         if 'bead_calibration_fn' in experiment.metadata[channel]]
                
                for channel, calibration_fn in beads:
                    tube_data[channel] = calibration_fn(tube_data[channel])

                tubes[tube_file] = tube_data

                
            data = tubes[tube_file][[from_channel, to_channel]]
            data = data[data[from_channel] > 0]
            data = data[data[to_channel] > 0]
            _ = data.reset_index(drop = True, inplace = True)

            if self.mixture_model:    
                gmm = sklearn.mixture.GMM(n_components=2)
                fit = gmm.fit(np.log10(data[from_channel][:, np.newaxis]))
    
                # pick the component with the maximum mean
                mu_idx = 0 if fit.means_[0][0] > fit.means_[1][0] else 1
                weights = [x[mu_idx] for x in fit.predict_proba(np.log10(data[from_channel][:, np.newaxis]))]
            else:
                weights = [1] * len(data.index)
                
            lr = np.polyfit(np.log10(data[from_channel]), 
                            np.log10(data[to_channel]), 
                            deg = 1, 
                            w = weights)
            
            self._coefficients[(from_channel, to_channel)] = lr


    def apply(self, experiment):
        """Applies the color translation to an experiment
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment with the color translation applied.
        """

        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        if not self._coefficients:
            raise CytoflowOpError("Coefficients aren't set. "
                                  "Did you call estimate()?")
            
        exp_channels = [x for x in experiment.metadata 
                        if 'type' in experiment.metadata[x] 
                        and experiment.metadata[x]['type'] == "channel"]
        
        if not set(self.translation.keys()) <= set(exp_channels):
            raise CytoflowOpError("Translation keys don't match "
                                  "experiment channels")
        
        if not set(self.translation.values()) <= set(exp_channels):
            raise CytoflowOpError("Translation values don't match "
                                  "experiment channels")
        
        for key, val in self.translation.iteritems():
            if (key, val) not in self._coefficients:
                raise CytoflowOpError("Coefficients aren't set for translation "
                                      "{1} --> {2}.  Did you call estimate()?"
                                      .format(key, val))
       
        new_experiment = experiment.clone()
        for from_channel, to_channel in self.translation.iteritems():
            coeff = self._coefficients[(from_channel, to_channel)]
            
            # remember, these (linear) coefficients came from logspace, so 
            # if the relationship in log10 space is Y = aX + b, then in
            # linear space the relationship is x = 10**X, y = 10**Y,
            # and y = (10**b) * x ^ a
            
            # also remember that the result of np.polyfit is a list of
            # coefficients with the highest power first!  so if we
            # solve y=ax + b, coeff #0 is a and coeff #1 is b
            
            a = coeff[0]
            b = 10 ** coeff[1]
            trans_fn = lambda x, a=a, b=b: b * np.power(x, a)
            
            new_experiment[from_channel] = trans_fn(experiment[from_channel])
            new_experiment.metadata[from_channel]['channel_translation_fn'] = trans_fn
            new_experiment.metadata[from_channel]['channel_translation'] = to_channel

        return new_experiment
    
    def default_view(self):
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """
        
        for tube_file in self.controls.values():  
            try:
                # suppress the channel name warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")

                    _ = fcsparser.parse(tube_file, 
                                        meta_data_only = True, 
                                        reformat_meta = True)
            except Exception as e:
                raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(tube_file, str(e)))

        return ColorTranslationDiagnostic(op = self)
    
@provides(IView)
class ColorTranslationDiagnostic(HasStrictTraits):
    """
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
    
    op : Instance(ColorTranslationOp)
        The op whose parameters we're viewing
    """
    
    # traits   
    id = "edu.mit.synbio.cytoflow.view.colortranslationdiagnostic"
    friendly_id = "Color Translation Diagnostic" 
    
    name = Str
    
    # TODO - why can't I use ColorTranslationOp here?
    op = Instance(IOperation)
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots
        """
        
        if not experiment:
            raise CytoflowViewError("No experiment specified")
        
        exp_channels = [x for x in experiment.metadata 
                        if 'type' in experiment.metadata[x] 
                        and experiment.metadata[x]['type'] == "channel"]
        
        tubes = {}
        
        plt.figure()
        num_plots = len(self.op.translation.keys())
        plt_idx = 0
        
        for from_channel, to_channel in self.op.translation.iteritems():
            
            if (from_channel, to_channel) not in self.op.controls:
                raise CytoflowOpError("Control file for {0} --> {1} not specified"
                                   .format(from_channel, to_channel))
            tube_file = self.op.controls[(from_channel, to_channel)]
            
            if tube_file not in tubes: 
                
                try:
                    channel_naming = experiment.metadata["name_meta"]
                    _, tube_data = \
                        fcsparser.parse(tube_file,
                                        reformat_meta = True,
                                        channel_naming = channel_naming)
                except Exception as e:
                    raise CytoflowOpError("FCS reader threw an error on tube {0}: {1}"\
                                       .format(tube_file, str(e)))
                
                # autofluorescence correction
                af = [(channel, (experiment.metadata[channel]['af_median'],
                                 experiment.metadata[channel]['af_stdev'])) 
                      for channel in exp_channels 
                      if 'af_median' in experiment.metadata[channel]]
                
                for af_channel, (af_median, af_stdev) in af:
                    tube_data[af_channel] = tube_data[af_channel] - af_median
                    tube_data = tube_data[tube_data[af_channel] > -3 * af_stdev]
                    
                tube_data.reset_index(drop = True, inplace = True)
                    
                # bleedthrough correction
                old_tube_data = tube_data.copy()
                bleedthrough = \
                    {channel: experiment.metadata[channel]['piecewise_bleedthrough']
                     for channel in exp_channels
                     if 'piecewise_bleedthrough' in experiment.metadata[channel]} 

                for channel, (interp_channels, interpolator) in bleedthrough.iteritems():
                    interp_data = old_tube_data[interp_channels]
                    tube_data[channel] = interpolator(interp_data)
                    
                # bead calibration
                beads = [(channel, experiment.metadata[channel]['bead_calibration_fn'])
                         for channel in exp_channels
                         if 'bead_calibration_fn' in experiment.metadata[channel]]
                
                for channel, calibration_fn in beads:
                    tube_data[channel] = calibration_fn(tube_data[channel])

                tubes[tube_file] = tube_data
                
            from_range = experiment.metadata[from_channel]['range']
            to_range = experiment.metadata[to_channel]['range']
            data = tubes[tube_file][[from_channel, to_channel]]
            data = data[data[from_channel] > 0]
            data = data[data[to_channel] > 0]
            _ = data.reset_index(drop = True, inplace = True)

            if self.op.mixture_model:    
                plt.subplot(num_plots, 2, plt_idx * 2 + 2)
                plt.xscale('log', nonposx='mask')
                hist_bins = np.logspace(1, math.log(from_range, 2), num = 128, base = 2)
                _ = plt.hist(data[from_channel],
                             bins = hist_bins,
                             histtype = 'stepfilled',
                             antialiased = True)
                plt.xlabel(from_channel)
                
                gmm = sklearn.mixture.GMM(n_components=2)
                fit = gmm.fit(np.log10(data[from_channel][:, np.newaxis]))
    
                mu_idx = 0 if fit.means_[0][0] > fit.means_[1][0] else 1
                weights = [x[mu_idx] for x in fit.predict_proba(np.log10(data[from_channel][:, np.newaxis]))]
                
                plt.axvline(10 ** fit.means_[0][0], color = 'r')
                plt.axvline(10 ** fit.means_[1][0], color = 'r')
            else:
                weights = [1] * len(data.index)
                
            lr = np.polyfit(np.log10(data[from_channel]), 
                            np.log10(data[to_channel]), 
                            deg = 1, 
                            w = weights)
            
            num_cols = 2 if self.op.mixture_model else 1
            plt.subplot(num_plots, num_cols, plt_idx * num_cols + 1)
            plt.xscale('log', nonposx = 'mask')
            plt.yscale('log', nonposy = 'mask')
            plt.xlabel(from_channel)
            plt.ylabel(to_channel)
            plt.xlim(1, from_range)
            plt.ylim(1, to_range)
            
            kwargs.setdefault('alpha', 0.2)
            kwargs.setdefault('s', 1)
            kwargs.setdefault('marker', 'o')
            
            plt.scatter(data[from_channel],
                        data[to_channel],
                        **kwargs)          

            xs = np.logspace(1, math.log(from_range, 2), num = 256, base = 2)
            p = np.poly1d(lr)
            plt.plot(xs, 10 ** p(np.log10(xs)), "--g")
            
            plt_idx = plt_idx + 1

'''
Created on Sep 2, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Python, \
                       Instance, Int, Tuple, Bool
import numpy as np
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation
import FlowCytometryTools as fc
import matplotlib.pyplot as plt
import seaborn
import math

import sklearn.mixture

from ..views import IView
from bleedthrough_piecewise import correct_bleedthrough

@provides(IOperation)
class ColorTranslationOp(HasStrictTraits):
    """
    Translate measurements from one color's scale to another, using a two-color
    or three-color control.
    
    To use, set up the `channels` dict with the desired mapping and the 
    `controls` dict with the multi-color controls.  Call `estimate()` to
    populate the `mapping` dict; check that the plots look good with 
    `default_view()`; then `apply()` to an Experiment.

    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation.)
        
    translation : Dict(Str, Str)
        Specifies the desired translation.  The keys are the channel names
        to map *from*; the values are the channel names to map *to*.
        
    controls : Dict((Str, Str), File)
        Two-color controls used to determine the mapping.  They keys are 
        tuples of *from-channel* and *to-channel* (corresponding to key-value
        pairs in `translation`).  They values are FCS files containing two-color 
        constitutive fluorescent expression for the mapping.
        
    subset : Int (default = 30,000)
        How many cells from each control file to take.
        
    mixture_model : Bool (default = False)
        If "True", try to model the "from" channel as a mixture of expressing
        cells and non-expressing cells (as you would get with a transient
        transfection.)  Make sure you check the diagnostic plots!
        
    coefficients : Dict((Str, Str), List(Float))
        The regression coefficients determined by `estimate()`, used to map 
        colors between channels.  The keys are tuples of (*from-channel*,
        *to-channel) (corresponding to key-value pairs in `translation`).  The
        values are lists of Float, the log-log coefficients for the color 
        translation (determined by `estimate()`).        
    """
    
    # traits
    id = "edu.mit.synbio.cytoflow.operations.color_translation"
    friendly_id = "Color translation"
    
    name = CStr()

    translation = Dict(Str, Str)
    controls = Dict(Tuple(Str, Str), File, transient = True)
    subset = Int(10000, transient = True)
    mixture_model = Bool(False, transient = True)

    coefficients = Dict(Tuple(Str, Str), Python)
    
    def is_valid(self, experiment):
        """Validate this operation against an experiment."""

        if not self.name:
            return False
        
        # NOTE: these conditions are for applying the correction, NOT estimating
        # the correction from controls.
        
        if not self.coefficients:
            return False
        
        if not set(self.translation.keys()) <= set(experiment.channels):
            return False
        
        if not set(self.translation.values()) <= set(experiment.channels):
            return False
        
        for key, val in self.translation.iteritems():
            if (key, val) not in self.coefficients:
                return False
       
        return True
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the mapping from the two-channel controls
        """
        
        tubes = {}
        
        for from_channel, to_channel in self.translation.iteritems():
            
            if (from_channel, to_channel) not in self.controls:
                raise RuntimeError("Control file for {0} --> {1} not specified"
                                   .format(from_channel, to_channel))
            tube_file = self.controls[(from_channel, to_channel)]
            
            if tube_file not in tubes: 
                tube = fc.FCMeasurement(ID='{0}.{1}'.format(from_channel, to_channel),
                                        datafile = tube_file) \
                                        .subsample(self.subset, "random")
                                    
                try:
                    tube.read_meta()
                except Exception:
                    raise RuntimeError("FCS reader threw an error on tube {0}"
                                       .format(self.controls[(from_channel, to_channel)]))
    
                tube_data = tube.data
                
                # autofluorescence correction
                af = [(channel, experiment.metadata[channel]['af_median']) 
                      for channel in experiment.channels 
                      if 'af_median' in experiment.metadata[channel]]
                
                for af_channel, af_value in af:
                    tube_data[af_channel] = tube_data[af_channel] - af_value
                    
                # bleedthrough correction
                splines = {channel: experiment.metadata[channel]['piecewise_bleedthrough']
                           for channel in experiment.channels
                           if 'piecewise_bleedthrough' in experiment.metadata[channel]}    
                
                tube_data = tube_data.apply(correct_bleedthrough,
                                  axis = 1,
                                  args = ([splines.keys(), splines]))
                
                tubes[tube_file] = tube_data
                
            data = tubes[tube_file][[from_channel, to_channel]]
            data = data[data[from_channel] > 0]
            data = data[data[to_channel] > 0]
            _ = data.reset_index(drop = True, inplace = True)

            if self.mixture_model:    
                gmm = sklearn.mixture.GMM(n_components=2)
                fit = gmm.fit(np.log10(data[from_channel][:, np.newaxis]))
    
                mu_idx = 0 if fit.means_[0][0] > fit.means_[1][0] else 1
                weights = [x[mu_idx] for x in fit.predict_proba(np.log10(data[from_channel][:, np.newaxis]))]
            else:
                weights = [1] * len(data.index)
                
            lr = np.polyfit(np.log10(data[from_channel]), 
                            np.log10(data[to_channel]), 
                            deg = 1, 
                            w = weights)
            
            self.coefficients[(from_channel, to_channel)] = lr


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

        new_experiment = old_experiment.clone()

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
            tube = fc.FCMeasurement(ID="beads", datafile = tube_file)

        try:
            tube.read_meta()
        except Exception:
            raise RuntimeError("FCS reader threw an error on tube {0}".format(self.beads_file))

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
        
        tubes = {}
        
        plt.figure()
        num_plots = len(self.op.translation.keys())
        plt_idx = 0
        
        for from_channel, to_channel in self.op.translation.iteritems():
            
            if (from_channel, to_channel) not in self.op.controls:
                raise RuntimeError("Control file for {0} --> {1} not specified"
                                   .format(from_channel, to_channel))
            tube_file = self.op.controls[(from_channel, to_channel)]
            
            if tube_file not in tubes: 
                tube = fc.FCMeasurement(ID='{0}.{1}'.format(from_channel, to_channel),
                                        datafile = tube_file) \
                                        .subsample(self.op.subset, "random")
                                    
                try:
                    tube.read_meta()
                except Exception:
                    raise RuntimeError("FCS reader threw an error on tube {0}"
                                       .format(self.op.controls[(from_channel, to_channel)]))
    
                tube_data = tube.data
                
                # autofluorescence correction
                af = [(channel, experiment.metadata[channel]['af_median']) 
                      for channel in experiment.channels 
                      if 'af_median' in experiment.metadata[channel]]
                
                for af_channel, af_value in af:
                    tube_data[af_channel] = tube_data[af_channel] - af_value
                    
                # bleedthrough correction
                splines = {channel: experiment.metadata[channel]['piecewise_bleedthrough']
                           for channel in experiment.channels
                           if 'piecewise_bleedthrough' in experiment.metadata[channel]}    
                
                tube_data = tube_data.apply(correct_bleedthrough,
                                  axis = 1,
                                  args = ([splines.keys(), splines]))
                
                tubes[tube_file] = tube_data
                
            data_range = experiment.metadata[channel]['range']
            data = tubes[tube_file][[from_channel, to_channel]]
            data = data[data[from_channel] > 0]
            data = data[data[to_channel] > 0]
            _ = data.reset_index(drop = True, inplace = True)

            if self.op.mixture_model:    
                plt.subplot(num_plots, 2, plt_idx * 2 + 2)
                plt.xscale('log', nonposx='mask')
                hist_bins = np.logspace(1, math.log(data_range, 2), num = 128, base = 2)
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
            plt.xlim(1, data_range)
            plt.ylim(1, data_range)
            plt.scatter(data[from_channel],
                        data[to_channel],
                        alpha = 0.2,
                        s = 1,
                        marker = 'o')
            

            xs = np.logspace(1, math.log(data_range, 2), num = 256, base = 2)
            p = np.poly1d(lr)
            plt.plot(xs, 10 ** p(np.log10(xs)), "--g")
            
            plt_idx = plt_idx + 1

    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        
        return self.op.is_valid(experiment)
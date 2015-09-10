'''
Created on Sep 2, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, CInt, File, Dict, Python, \
                       Instance, Int, CFloat, Tuple
import numpy as np
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation
import FlowCytometryTools as fc
import math
import scipy.interpolate
import scipy.optimize
import matplotlib as mpl
import matplotlib.pyplot as plt

from ..views import IView
from bleedthrough_piecewise import correct_bleedthrough

@provides(IOperation)
class ColorTranslationOp(HasStrictTraits):
    """
    Translate measurements from one colors' scale to another.
    
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
    coefficients = Dict((Str, Str), Python)
    controls = Dict(Tuple(Str, Str), File, transient = True)
    
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
        
        for from_channel, to_channel in self.translation.iteritems():
            
            if (from_channel, to_channel) not in self.controls:
                raise RuntimeError("Control file for {0} --> {1} not specified"
                                   .format(from_channel, to_channel))
            tube_file = self.controls[(from_channel, to_channel)]
            tube = fc.FCMeasurement(ID='{0}.{1}'.format(from_channel, to_channel),
                                    datafile = tube_file)
            try:
                tube.read_meta()
            except Exception:
                raise RuntimeError("FCS reader threw an error on tube {0}"
                                   .format(self.controls[(from_channel, to_channel)]))

            data = tube.data
            
            # autofluorescence correction
            af = [(channel, experiment.metadata[channel]['af_median']) 
                  for channel in experiment.channels 
                  if 'af_median' in experiment.metadata[channel]]
            
            for af_channel, af_value in af:
                data[af_channel] = data[af_channel] - af_value
                
            # bleedthrough correction
            splines = {channel: experiment.metadata[channel]['piecewise_bleedthrough']
                       for channel in experiment.channels
                       if 'piecewise_bleedthrough' in experiment.metadata[channel]}    
            
            data = data.apply(correct_bleedthrough,
                              axis = 1,
                              args = ([splines.keys(), splines]))
            
            plt.figure()
            plt.xscale('log', nonposx='mask')
            plt.yscale('log', nonposy='mask')
            plt.xlim(1, 10**6)
            plt.ylim(1, 10**6)
            
            plt.scatter(data[from_channel], data[to_channel],
                        alpha = 0.02, s = 1, marker = 'o')
            # estimate the translation coefficients with a linear fit to 
            # log-space data
            
            lr = np.polyfit(np.log10(data[from_channel]),
                            np.log10(data[to_channel]),
                            deg = 1)
            
            self.coefficients[(from_channel, to_channel)] = lr
            
            p = np.poly1d(lr)
            xs = np.logspace(1, 6, base=10)
            plt.plot(xs, 10**p(np.log10(xs)), "--k")
            
            plt.show()

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
        

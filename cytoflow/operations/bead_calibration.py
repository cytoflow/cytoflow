'''
Created on Aug 31, 2015

@author: brian
'''


from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, CInt, File, Dict, Python, \
                       Instance, Int, CFloat, List, Float
import numpy as np
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation
from ..views import IView
import FlowCytometryTools as fc
import math
import scipy.interpolate
import scipy.optimize

@provides(IOperation)
class BeadCalibrationOp(HasStrictTraits):
    """
    Calibrate arbitrary units to molecules-of-fluorophore using fluorescent
    beads (eg, the Spherotech RCP-30-5A.)
    
    To use, set the `beads_file` property to an FCS file containing the beads'
    events; specify which beads you ran by setting the `beads_type` property
    to match on of the keys in BeadCalibrationOp.BeadTypes; and set the
    `channels` dict to which channels you want calibrated and in which units.
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation.)

    channels : Dict(Str, Str)
        A dictionary specifying the channels you want calibrated (keys) and
        the units you want them calibrated in (values).  The units must be
        keys of `beads`.
        
    calibration : Dict(Str, Python)
        Not sure yet what this will look like. Keys are channels to calibrate.
        
    beads_file : File
        A file containing the FCS events from the beads.  Must be set to use
        `estimate()`.  This isn't persisted by `pickle()`.
        
    forward_scatter_channel : Str
        The channel name for forward scatter. Must be set to use `estimate()`.
        
    side_scatter_channel : Str
        The channel name for side scatter.  Must be set to use `estimate()`.
        
    beads : Dict(Str, List(Float))
        The beads' characteristics.  Keys are calibrated units (ie, MEFL or
        MEAP) and values are ordered lists of known fluorophore levels.  Common
        values for this dict are included in BeadCalibrationOp.BEADS.
        Must be set to use `estimate()`.

    """
    
    # traiats
    id = 'edu.mit.synbio.cytoflow.operations.beads_calibrate'
    friendly_id = "Bead Calibration"
    
    name = CStr()
    channels = Dict(Str, Str)
    calibration = Dict(Str, Python)
    
    beads_file = File(transient = True)
    forward_scatter_channel = Str(transient = True)
    side_scatter_channel = Str(transient = True)
    beads = Dict(Str, List(Float), transient = True)
    
    def is_valid(self, experiment):
        """Validate this operation against an experiment."""

        return False
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the calibration coefficients from the beads file.
        """


    def apply(self, old_experiment):
        """Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old_experiment to which this op is applied
            
        Returns
        -------
            a new experiment calibrated in physical units.
        """
    
    def default_view(self):
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """

        return BeadCalibrationDiagnostic(op = self)
    
    BEADS = {
             # from http://www.spherotech.com/RCP-30-5a%20%20rev%20H%20ML%20071712.xls
             "Spherotech RCP-30-5A Lot AG01, AF02, AD04 and AAE01" :
                { "MECSB" : [216, 464, 1232, 2940, 7669, 19812, 35474],
                  "MEBFP" : [861, 1997, 5776, 15233, 45389, 152562, 396759],
                  "MEFL" :  [792, 2079, 6588, 16471, 47497, 137049, 271647],
                  "MEPE" :  [531, 1504, 4819, 12506, 36159, 109588, 250892],
                  "MEPTR" : [233, 669, 2179, 5929, 18219, 63944, 188785],
                  "MECY5" : [1614, 4035, 12025, 31896, 95682, 353225, 1077421],
                  "MEPCY7" : [14916, 42336, 153840, 494263],
                  "MEAP" : [373, 1079, 3633, 9896, 28189, 79831, 151008],
                  "MEAPCY7" : [2864, 7644, 19081, 37258]}}
    
@provides(IView)
class BeadCalibrationDiagnostic(HasStrictTraits):
    """
    Plots a scatterplot of the forward/side scatter channels
    
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
    
    # TODO - why can't I use BeadCalibrationOp here?
    op = Instance(IOperation)
    
    def plot(self, experiment = None, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        import matplotlib.pyplot as plt
        
        kwargs.setdefault('histtype', 'stepfilled')
        kwargs.setdefault('alpha', 0.5)
        kwargs.setdefault('antialiased', True)
         
        plt.figure()

    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        
        return self.op.is_valid(experiment)

    


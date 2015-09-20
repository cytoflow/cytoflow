'''
Created on Aug 31, 2015

@author: brian
'''


from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Python, \
                       Instance, Int, List, Float
import numpy as np
from traits.has_traits import provides
from cytoflow.operations.i_operation import IOperation
from ..views import IView
import FlowCytometryTools as fc
import math
import scipy.signal

@provides(IOperation)
class BeadCalibrationOp(HasStrictTraits):
    """
    Calibrate arbitrary units to molecules-of-fluorophore using fluorescent
    beads (eg, the Spherotech RCP-30-5A.)
    
    To use, set the `beads_file` property to an FCS file containing the beads'
    events; specify which beads you ran by setting the `beads_type` property
    to match on of the keys in BeadCalibrationOp.BeadTypes; and set the
    `channels` dict to which channels you want calibrated and in which units.
    
    This procedure works best when the beads file is very clean data. 
    Recommend gating the acquisition on the FSC/SSC channels in order
    to get rid of debris and noise.
    
    Attributes
    ----------
    name : Str
        The operation name (for UI representation.)

    units : Dict(Str, Str)
        A dictionary specifying the channels you want calibrated (keys) and
        the units you want them calibrated in (values).  The units must be
        keys of `beads`.       
        
    calibration : Dict(Str, Python)
        Keys are channels to calibrate; values are the coefficient by which
        to multiply the input values (either a `Float` or a 2-list of `Float`s).
        
    beads_file : File
        A file containing the FCS events from the beads.  Must be set to use
        `estimate()`.  This isn't persisted by `pickle()`.
        
    bead_peak_quantile : Int
        The quantile threshold used to choose bead peaks.  Default == 80.
        Must be set to use `estimate()`.
        
    bead_brightness_threshold : Float
        How bright must a bead peak be to be considered?  Default == 100.
        Must be set to use `estimate()`.  TODO - this should probably be
        different depending on the data range of the input.
        
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
    units = Dict(Str, Str)
    _coefficients = Dict(Str, Python)
    
    beads_file = File(transient = True)
    bead_peak_quantile = Int(80)
    bead_brightness_threshold = Float(100)
    beads = Dict(Str, List(Float), transient = True)
    
    def is_valid(self, experiment):
        """Validate this operation against an experiment."""

        if not self.units or not self._calibration:
            return False
        
        channels = self.units.keys()
        if not set(self.units.keys()) <= set(experiment.channels):
            return False
                
        if set(channels) != set(self._coefficients.keys()):
            return False
        
        if not set(self.units.values()) <= set(self.beads.keys()):
            return False

        return True
    
    def estimate(self, experiment, subset = None): 
        """
        Estimate the calibration coefficients from the beads file.
        """
        
        beads_tube = fc.FCMeasurement(ID='blank', datafile = self.beads_file)
        channels = self.units.keys()
        
        try:
            beads_tube.read_meta()
        except Exception:
            raise RuntimeError("FCS reader threw an error on tube {0}".format(self.beads_file))

        # make sure the voltages didn't change
        
        for channel in channels:
            exp_v = experiment.metadata[channel]['voltage']
        
            if not "$PnV" in beads_tube.channels:
                raise RuntimeError("Didn't find a voltage for channel {0}" \
                                   "in tube {1}".format(channel, self.beads_file))
            
            control_v = beads_tube.channels[beads_tube.channels['$PnN'] == channel]['$PnV'].iloc[0]
            
            if control_v != exp_v:
                raise RuntimeError("Voltage differs for channel {0} in tube {1}"
                                   .format(channel, self.beads_file))
    

        for channel in channels:
            data = beads_tube.data[channel]
            
            # bin the data on a log scale
            data_range = experiment.metadata[channel]['range']
            hist_bins = np.logspace(1, math.log(data_range, 2), num = 256, base = 2)
            hist = np.histogram(data, bins = hist_bins)
            
            # mask off-scale values
            hist[0][0] = 0
            hist[0][-1] = 0
            
            # smooth it with a Savitzky-Golay filter
            hist_smooth = scipy.signal.savgol_filter(hist[0], 5, 1)
            
            # find peaks
            peak_bins = scipy.signal.find_peaks_cwt(hist_smooth, 
                                                    widths = np.arange(3, 20),
                                                    max_distances = np.arange(3, 20) / 2)
            
            # filter by height and intensity
            peak_threshold = np.percentile(hist_smooth, self.bead_peak_quantile)
            peak_bins_filtered = \
                [x for x in peak_bins if hist_smooth[x] > peak_threshold 
                 and hist[1][x] > self.bead_brightness_threshold]
            
            peaks = [hist_bins[x] for x in peak_bins_filtered]
            
            mef_unit = self.units[channel]
            
            if not mef_unit in self.beads:
                raise RuntimeError("Invalid unit {0} specified for channel {1}".format(mef_unit, channel))
            
            # "mean equivalent fluorochrome"
            mef = self.beads[mef_unit]
            
            if len(peaks) == 0:
                raise RuntimeError("Didn't find any peaks; check the diagnostic plot")
            elif len(peaks) > len(self.beads):
                raise RuntimeError("Found too many peaks; check the diagnostic plot")
            elif len(peaks) == 1:
                # if we only have one peak, assume it's the brightest peak
                self._coefficients[channel] = [mef[-1] / peaks[0]] 
            elif len(peaks) == 2:
                # if we have only two peaks, assume they're the brightest two
                self._coefficients[channel] = \
                    [(mef[-1] - mef[-2]) / (peaks[1] - peaks[0])]
            else:
                # if there are n > 2 peaks, check all the contiguous n-subsets
                # of mef for the one whose linear regression with the peaks
                # has the smallest (norm) sum-of-residuals.
                
                # do it in log10 space because otherwise the brightest peaks
                # have an outsized influence.
                
                best_resid = np.inf
                for start, end in [(x, x+len(peaks)) for x in range(len(mef) - len(peaks) + 1)]:
                    mef_subset = mef[start:end]
                    
                    # linear regression of the peak locations against mef subset
                    lr = np.polyfit(np.log10(peaks), 
                                    np.log10(mef_subset), 
                                    deg = 1, 
                                    full = True)
                    
                    resid = lr[1][0]
                    if resid < best_resid:
                        best_lr = lr[0]
                        best_resid = resid
                        
                self._coefficients[channel] = (best_lr[0], best_lr[1])

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
        
        channels = self._coefficients.keys()
        new_experiment = old_experiment.clone()
        
        # two things.  first, you can't raise a negative value to a non-integer
        # power.  second, negative physical units don't make sense -- how can
        # you have the equivalent of -5 molecules of fluoresceine?  so,
        # we filter out negative values here.
        
        for channel in channels:
            new_experiment.data = \
                new_experiment.data[new_experiment.data[channel] > 0]
                
        new_experiment.data.reset_index(drop = True, inplace = True)
        
        for channel in channels:
            if len(self._coefficients[channel]) == 1:
                # plain old multiplication
                a = self._coefficients[channel][0]
                calibration_fn = lambda x, a=a: a * x
            else:
                # remember, these (linear) coefficients came from logspace, so 
                # if the relationship in log10 space is Y = aX + b, then in
                # linear space the relationship is x = 10**X, y = 10**Y,
                # and y = (10**b) * x ^ a
                
                # also remember that the result of np.polyfit is a list of
                # coefficients with the highest power first!  so if we
                # solve y=ax + b, coeff #0 is a and coeff #1 is b
                a = self._coefficients[channel][0]
                b = 10 ** self._coefficients[channel][1]
                calibration_fn = lambda x, a=a, b=b: b * np.power(x, a)
    
            new_experiment[channel] = calibration_fn(new_experiment[channel])
            new_experiment.metadata[channel]['bead_calibration_fn'] = calibration_fn
            new_experiment.metadata[channel]['units'] = self.units[channel]
            
        return new_experiment
    
    def default_view(self):
        """
        Returns a diagnostic plot to see if the bleedthrough spline estimation
        is working.
        
        Returns
        -------
            IView : An IView, call plot() to see the diagnostic plots
        """
        
        beads_tube = fc.FCMeasurement(ID="beads",
                              datafile = self.beads_file)

        try:
            beads_tube.read_meta()
        except Exception:
            raise RuntimeError("FCS reader threw an error on tube {0}".format(self.beads_file))

        return BeadCalibrationDiagnostic(op = self)
    
    BEADS = {
             # from http://www.spherotech.com/RCP-30-5a%20%20rev%20H%20ML%20071712.xls
             "Spherotech RCP-30-5A Lot AG01, AF02, AD04 and AAE01" :
                { "MECSB" : [216, 464, 1232, 2940, 7669, 19812, 35474],
                  "MEBFP" : [861, 1997, 5776, 15233, 45389, 152562, 396759],
                  "MEFL" :  [792, 2079, 6588, 16471, 47497, 137049, 271647],
                  "MEPE" :  [531, 1504, 4819, 12506, 36159, 109588, 250892],
                  "MEPTR" : [233, 669, 2179, 5929, 18219, 63944, 188785],
                  "MECY" : [1614, 4035, 12025, 31896, 95682, 353225, 1077421],
                  "MEPCY7" : [14916, 42336, 153840, 494263],
                  "MEAP" :  [373, 1079, 3633, 9896, 28189, 79831, 151008],
                  "MEAPCY7" : [2864, 7644, 19081, 37258]},
             # from http://www.spherotech.com/RCP-30-5a%20%20rev%20G.2.xls
             "Spherotech RCP-30-5A Lot AA01-AA04, AB01, AB02, AC01, GAA01-R":
                { "MECSB" : [179, 400, 993, 3203, 6083, 17777, 36331],
                  "MEBFP" : [700, 1705, 4262, 17546, 35669, 133387, 412089],
                  "MEFL" :  [692, 2192, 6028, 17493, 35674, 126907, 290983],
                  "MEPE" :  [505, 1777, 4974, 13118, 26757, 94930, 250470],
                  "MEPTR" : [207, 750, 2198, 6063, 12887, 51686, 170219],
                  "MECY" :  [1437, 4693, 12901, 36837, 76621, 261671, 1069858],
                  "MEPCY7" : [32907, 107787, 503797],
                  "MEAP" :  [587, 2433, 6720, 17962, 30866, 51704, 146080],
                  "MEAPCY7" : [718, 1920, 5133, 9324, 14210, 26735]}}
    
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
    
    def plot(self, experiment, **kwargs):
        """Plot a faceted histogram view of a channel"""
        
        beads_tube = fc.FCMeasurement(ID="beads",
                                      datafile = self.op.beads_file)
        
        import matplotlib.pyplot as plt
        import seaborn

         
        plt.figure()
        
        channels = self.op.units.keys()
        
        for idx, channel in enumerate(channels):
            data = beads_tube.data[channel]
            
            # bin the data on a log scale
            data_range = experiment.metadata[channel]['range']
            hist_bins = np.logspace(1, math.log(data_range, 2), num = 256, base = 2)
            hist = np.histogram(data, bins = hist_bins)
            
            # mask off-scale values
            hist[0][0] = 0
            hist[0][-1] = 0
            
            hist_smooth = scipy.signal.savgol_filter(hist[0], 5, 1)
            
            # find peaks
            peak_bins = scipy.signal.find_peaks_cwt(hist_smooth, 
                                                    widths = np.arange(3, 20),
                                                    max_distances = np.arange(3, 20) / 2)
            
            # filter by height and intensity
            peak_threshold = np.percentile(hist_smooth, self.op.bead_peak_quantile)
            peak_bins_filtered = \
                [x for x in peak_bins if hist_smooth[x] > peak_threshold
                 and hist[1][x] > self.op.bead_brightness_threshold]
                
            plt.subplot(len(channels), 1, idx+1)
            plt.xscale('log')
            plt.xlabel(channel)
            plt.plot(hist_bins[1:], hist_smooth)
            for peak in peak_bins_filtered:
                plt.axvline(hist_bins[peak], color = 'r')
            

    def is_valid(self, experiment):
        """Validate this view against an experiment."""
        
        return self.op.is_valid(experiment)
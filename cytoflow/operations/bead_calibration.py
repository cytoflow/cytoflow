#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflow.operations.bead_calibration
------------------------------------

The `bead_calibration` module contains two classes:

`BeadCalibrationOp` -- calibrates the raw measurements in a
`Experiment` using fluorescent particles.

`BeadCalibrationDiagnostic` -- a diagnostic view to make sure
that `BeadCalibrationOp` correctly estimated its parameters.
"""

from traits.api import (HasStrictTraits, Str, File, Dict, Bool, Int, List, 
                        Float, Constant, provides, Callable, Any,
                        Instance)
import numpy as np
import math
import scipy.signal
import scipy.optimize
        
import matplotlib.pyplot as plt

import cytoflow.views
import cytoflow.utility as util

from .i_operation import IOperation
from .import_op import check_tube, Tube, ImportOp

@provides(IOperation)
class BeadCalibrationOp(HasStrictTraits):
    """
    Calibrate arbitrary channels to molecules-of-fluorophore using fluorescent
    beads (eg, the Spherotech RCP-30-5A rainbow beads.)
    
    Computes a log-linear calibration function that maps arbitrary fluorescence
    units to physical units (ie molecules equivalent fluorophore, or *MEF*).
    
    To use, set `beads_file` to an FCS file containing events collected *using
    the same cytometer settings as the data you're calibrating*.  Specify which 
    beads you ran by setting `beads` to match one of the  values of 
    `BeadCalibrationOp.BEADS`; and set `units` to which channels you 
    want calibrated and in which units.  Then, call `estimate` and check the 
    peak-finding with `BeadCalibrationDiagnostic.plot`.  If the peak-finding is wacky, 
    try adjusting `bead_peak_quantile` and `bead_brightness_threshold`.  When 
    the peaks are successfully identified, call `apply` to scale your 
    experimental data set. 
    
    If you can't make the peak finding work, please submit a bug report!
    
    This procedure works best when the beads file is very clean data.  It does
    not do its own gating (maybe a future addition?)  In the meantime, 
    I recommend gating the *acquisition* on the FSC/SSC channels in order
    to get rid of debris, cells, and other noise.
    
    Finally, because you can't have a negative number of fluorescent molecules
    (MEFLs, etc) (as well as for math reasons), this module filters out
    negative values.    
    
    Attributes
    ----------
    units : Dict(Str, Str)
        A dictionary specifying the channels you want calibrated (keys) and
        the units you want them calibrated in (values).  The units must be
        keys of the `beads` attribute.       
        
    beads_file : File
        A file containing the FCS events from the beads.

    beads : Dict(Str, List(Float))
        The beads' characteristics.  Keys are calibrated units (ie, MEFL or
        MEAP) and values are ordered lists of known fluorophore levels.  Common
        values for this dict are included in `BeadCalibrationOp.BEADS`.
        
    bead_peak_quantile : Int (default = 80)
        The quantile threshold used to choose bead peaks. 
        
    bead_brightness_threshold : Float (default = 100)
        How bright must a bead peak be to be considered?  
        
    bead_brightness_cutoff : Float
        If a bead peak is above this, then don't consider it.  Takes care of
        clipping saturated detection.  Defaults to 70% of the detector range.
        
    bead_histogram_bins : Int (default = 512)
        The number of bins to use in computing the bead histogram.  Tweak
        this if the peak find is having difficulty, or if you have a small 
        number of events
        
    force_linear : Bool (default = False)
        A linear fit in log space doesn't always go through the origin, which 
        means that the calibration function isn't strictly a multiplicative
        scaling operation.  Set `force_linear` to force the such
        behavior.  Keep an eye on the diagnostic plot, though, to see how much
        error you're introducing!
   
           
    Notes
    -----
    The peak finding is rather sophisticated.  
    
    For each channel, a 256-bin histogram is computed on the log-transformed
    bead data, and then the histogram is smoothed with a Savitzky-Golay 
    filter (with a window length of 5 and a polynomial order of 1).  
    
    Next, a wavelet-based peak-finding algorithm is used: it convolves the
    smoothed histogram with a series of wavelets and looks for relative 
    maxima at various length-scales.  The parameters of the smoothing 
    algorithm were arrived at empircally, using beads collected at a wide 
    range of PMT voltages.
    
    Finally, the peaks are filtered by height (the histogram bin has a quantile
    greater than `bead_peak_quantile`) and intensity (brighter than 
    `bead_brightness_threshold`).
    
    How to convert from a series of peaks to mean equivalent fluorochrome?
    If there's one peak, we assume that it's the brightest peak.  If there
    are two peaks, we assume they're the brightest two.  If there are ``n >=3``
    peaks, we check all the contiguous ``n``-subsets of the bead intensities
    and find the one whose linear regression (in log space!) has the smallest
    norm (square-root sum-of-squared-residuals.)
    
    There's a slight subtlety in the fact that we're performing the linear
    regression in log-space: if the relationship in log10-space is ``Y=aX + b``,
    then the same relationship in linear space is ``x = 10**X``, ``y = 10**y``, and
    ``y = (10**b) * (x ** a)``.
    
    .. note:: Adding a new set of beads is easy!  Please don't add them directly
              to `BEADS`, though -- instead, add them to ``beads.csv``, then run
              the `cytoflow.scripts.parse_beads` script to convert it into
              a dict.

    
    Examples
    --------
    Create a small experiment:
    
    .. plot::
        :context: close-figs
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "tasbe/rby.fcs")]
        >>> ex = import_op.apply()
    
    Create and parameterize the operation
    
    .. plot::
        :context: close-figs

        >>> bead_op = flow.BeadCalibrationOp()
        >>> beads = 'RCP-30-5A Lot AA01, AA02, AA03, AA04, AB01, AB02, AC01 & GAA01-R'
        >>> bead_op.beads = flow.BeadCalibrationOp.BEADS[beads]
        >>> bead_op.units = {"Pacific Blue-A" : "MEBFP",
        ...                  "FITC-A" : "MEFL",
        ...                  "PE-Tx-Red-YG-A" : "MEPTR"}
        >>>
        >>> bead_op.beads_file = "tasbe/beads.fcs"
    
    Estimate the model parameters
    
    .. plot::
        :context: close-figs 
    
        >>> bead_op.estimate(ex)
    
    Plot the diagnostic plot
    
    .. plot::
        :context: close-figs

        >>> bead_op.default_view().plot(ex)  

    Apply the operation to the experiment
    
    .. plot::
        :context: close-figs
    
        >>> ex = bead_op.apply(ex)  
        
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.beads_calibrate')
    friendly_id = Constant("Bead Calibration")
    
    name = Constant("Beads")
    units = Dict(Str, Str)
    
    beads_file = File(exists = True)
    bead_peak_quantile = Int(80)

    bead_brightness_threshold = Float(100.0)
    bead_brightness_cutoff = util.FloatOrNone(None)
    bead_histogram_bins = Int(512)
    
    # TODO - bead_brightness_threshold should probably be different depending
    # on the data range of the input.
    
    force_linear = Bool(False)
    
    beads = Dict(Str, List(Float))

    _histograms = Dict(Str, Any, transient = True)
    _calibration_functions = Dict(Str, Callable, transient = True)
    _peaks = Dict(Str, Any, transient = True)
    _mefs = Dict(Str, Any, transient = True)

    def estimate(self, experiment): 
        """
        Estimate the calibration coefficients from the beads file.
        
        Parameters
        ----------
        experiment : `Experiment`
            The experiment used to compute the calibration.
            
        """
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        if not self.beads_file:
            raise util.CytoflowOpError('beads_file', "No beads file specified")

        if not set(self.units.keys()) <= set(experiment.channels):
            raise util.CytoflowOpError('units',
                                       "Specified channels that weren't found in "
                                       "the experiment.")
            
        if not set(self.units.values()) <= set(self.beads.keys()):
            raise util.CytoflowOpError('units',
                                       "Units don't match beads.")
            
        self._histograms.clear()
        self._calibration_functions.clear()
        self._peaks.clear()
        self._mefs.clear()
                        
        # make a little Experiment
        check_tube(self.beads_file, experiment)
        beads_exp = ImportOp(tubes = [Tube(file = self.beads_file)],
                             channels = {experiment.metadata[c]["fcs_name"] : c for c in experiment.channels},
                             name_metadata = experiment.metadata['name_metadata']).apply()
        
        channels = list(self.units.keys())

        # make the histogram
        for channel in channels:
            data = beads_exp.data[channel]
            data_range = experiment.metadata[channel]['range']
                                     
            # bin the data on a log scale

            hist_bins = np.logspace(1, math.log(data_range, 2), num = self.bead_histogram_bins, base = 2)
            hist = np.histogram(data, bins = hist_bins)
            
            # mask off-scale values
            hist[0][0] = 0
            hist[0][-1] = 0
            
            # smooth it with a Savitzky-Golay filter
            hist_smooth = scipy.signal.savgol_filter(hist[0], 5, 1)
            
            self._histograms[channel] = (hist, hist_bins, hist_smooth)

            
        # find peaks
        for channel in channels:
            # TODO - this assumes the data is on a linear scale.  check it!
            data_range = experiment.metadata[channel]['range']

            if self.bead_brightness_cutoff is None:
                cutoff = 0.7 * data_range
            else:
                cutoff = self.bead_brightness_cutoff
                   
            hist = self._histograms[channel][0]
            hist_bins = self._histograms[channel][1]
            hist_smooth = self._histograms[channel][2]

            peak_bins = scipy.signal.find_peaks_cwt(hist_smooth, 
                                                    widths = np.arange(3, 20),
                                                    max_distances = np.arange(3, 20) / 2)
                                    
            # filter by height and intensity
            peak_threshold = np.percentile(hist_smooth, self.bead_peak_quantile)
            peak_bins_filtered = \
                [x for x in peak_bins if hist_smooth[x] > peak_threshold 
                 and hist[1][x] > self.bead_brightness_threshold
                 and hist[1][x] < cutoff]
            
            self._peaks[channel] = [hist_bins[x] for x in peak_bins_filtered]    


        # compute the conversion        
        calibration_functions = {}
        for channel in channels:
            peaks = self._peaks[channel]
            mef_unit = self.units[channel]
            
            if not mef_unit in self.beads:
                raise util.CytoflowOpError('units',
                                           "Invalid unit {0} specified for channel {1}".format(mef_unit, channel))
            
            # "mean equivalent fluorochrome"
            mef = self.beads[mef_unit]
                                                    
            if len(peaks) == 0:
                raise util.CytoflowOpError(None,
                                           "Didn't find any peaks for channel {}; "
                                           "check the diagnostic plot"
                                           .format(channel))
            elif len(peaks) > len(mef):
                raise util.CytoflowOpError(None,
                                           "Found too many peaks for channel {}; "
                                           "check the diagnostic plot"
                                           .format(channel))
            elif len(peaks) == 1:
                # if we only have one peak, assume it's the brightest peak
                a = mef[-1] / peaks[0]
                self._mefs[channel] = [mef[-1]]
                calibration_functions[channel] = lambda x, a=a: a * x
            elif len(peaks) == 2:
                # if we have only two peaks, assume they're the brightest two
                self._mefs[channel] = [mef[-2], mef[-1]]
                a = (mef[-1] - mef[-2]) / (peaks[1] - peaks[0])
                calibration_functions[channel] = lambda x, a=a: a * x
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
                        self._mefs[channel] = mef_subset
   
                if self.force_linear:
                    # if we're forcing a linear scale for the calibration
                    # function, find that scale with an optimization.  (we can't
                    # use this above, to find the MEFs from the peaks, because
                    # when i tried it mis-identified the proper subset.)
                    
                    # even though this keeps things a linear scale, it can
                    # actually introduce *more* errors because "blank" beads
                    # still fluoresce.
                    
                    def s(x):
                        p = np.multiply(self._peaks[channel], x)
                        return np.sum(np.abs(np.subtract(p, self._mefs[channel])))
                    
                    res = scipy.optimize.minimize(s, [1])
                    
                    a = res.x[0]
                    calibration_functions[channel] = \
                        lambda x, a=a: a * x
                              
                else:              
                    # remember, these (linear) coefficients came from logspace, so 
                    # if the relationship in log10 space is Y = aX + b, then in
                    # linear space the relationship is x = 10**X, y = 10**Y,
                    # and y = (10**b) * x ^ a
                    
                    # also remember that the result of np.polyfit is a list of
                    # coefficients with the highest power first!  so if we
                    # solve y=ax + b, coeff #0 is a and coeff #1 is b
                    
                    a = best_lr[0]
                    b = 10 ** best_lr[1]
                    calibration_functions[channel] = \
                        lambda x, a=a, b=b: b * np.power(x, a)
                        
        # set this atomically to support GUI
        self._calibration_functions = calibration_functions


    def apply(self, experiment):
        """
        Applies the bleedthrough correction to an experiment.
        
        Parameters
        ----------
        experiment : `Experiment`
            the experiment to which this operation is applied
            
        Returns
        -------
        Experiment 
            A new experiment with the specified channels calibrated in
            physical units.  The calibrated channels also have new metadata:
            
            - **bead_calibration_fn** : Callable (`pandas.Series` --> `pandas.Series`)
                The function to calibrate raw data to bead units
        
            - **bead_units** : Str
                The units this channel was calibrated to
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment', "No experiment specified")
        
        channels = list(self.units.keys())

        if not self.units:
            raise util.CytoflowOpError('units', "No channels to calibrate.")
        
        if not self._calibration_functions:
            raise util.CytoflowOpError(None,
                                       "Calibration not found. "
                                       "Did you forget to call estimate()?")
        
        if not set(channels) <= set(experiment.channels):
            raise util.CytoflowOpError('units',
                                       "Module units don't match experiment channels")
                
        if set(channels) != set(self._calibration_functions.keys()):
            raise util.CytoflowOpError('units',
                                       "Calibration doesn't match units. "
                                       "Did you forget to call estimate()?")

        # two things.  first, you can't raise a negative value to a non-integer
        # power.  second, negative physical units don't make sense -- how can
        # you have the equivalent of -5 molecules of fluoresceine?  so,
        # we filter out negative values here.

        new_experiment = experiment.clone(deep = True)
        
        for channel in channels:
            new_experiment.data = \
                new_experiment.data[new_experiment.data[channel] > 0]
                                
        new_experiment.data.reset_index(drop = True, inplace = True)
        
        for channel in channels:
            calibration_fn = self._calibration_functions[channel]
            
            new_experiment[channel] = calibration_fn(new_experiment[channel])
            new_experiment.metadata[channel]['bead_calibration_fn'] = calibration_fn
            new_experiment.metadata[channel]['bead_units'] = self.units[channel]
            if 'range' in experiment.metadata[channel]:
                new_experiment.metadata[channel]['range'] = calibration_fn(experiment.metadata[channel]['range'])
            if 'voltage' in experiment.metadata[channel]:
                del new_experiment.metadata[channel]['voltage']
            
        new_experiment.history.append(self.clone_traits(transient = lambda t: True)) 
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot to see if the peak finding is working.
        
        Returns
        -------
        `IView`
            An diagnostic view, call `BeadCalibrationDiagnostic.plot` to 
            see the diagnostic plots
        """

        v = BeadCalibrationDiagnostic(op = self)
        v.trait_set(**kwargs)
        return v
    
    # DON'T EDIT THIS DIRECTLY.  EDIT BEADS.CSV, THEN RUN PARSE_BEADS ON IT.
    
    BEADS = \
    {
        'ACP 30-2K': {
            'MEAP': [7880.0, 17400.0, 53100.0, 130000.0, 208000.0]
        },
        'RCP-30-5A Lot AN04, AN03, AN02, AN01, AM02, AM01, AL01, AK04, AK03 & AK02':
        {
            'MECSB': [
                205.139224587675, 470.418789207962, 1211.03409137091,
                2739.85605412079, 7516.43849705557, 20121.7589207813,
                35572.7129888405
            ],
            'MEBFP': [
                843.503722117931, 1957.71825828363, 5421.80193415564,
                13522.433084656, 42717.4973739119, 153501.022826764,
                420359.287816952
            ],
            'MEFL': [
                771.204227758779, 2106.46973727296, 6262.29508551021,
                15182.5413019226, 45291.7071432442, 136257.847794468,
                291041.740879689
            ],
            'MEPE': [
                487.398484275159, 1473.64215674594, 4516.24975517653,
                11260.0753555562, 34341.0801281963, 107608.01291543,
                260461.299924314
            ],
            'MEPTR': [
                204.868534691815, 643.202193579403, 2021.09484018683,
                5278.32442121266, 17017.8228394271, 62450.9816067639,
                198932.678535898
            ],
            'MECY': [
                1414.42033101552, 3808.80637667958, 10852.1944856379,
                27904.3884607569, 85866.2647607231, 324106.419847251,
                1040895.428772
            ],
            'MEPCY7': [
                12752.0445894082, 39056.5340076057, 142957.954887933,
                448890.055464371
            ],
            'MEAP': [
                341.010388310164, 1027.34896530879, 3155.71287209302,
                7750.10141500535, 23446.4537774744, 68701.80510944,
                116813.097393489
            ],
            'MEAPCY7': [
                173.309661734951, 427.442877227215, 1097.43242546677,
                2399.15279284361, 6359.25563563231, 17474.9563255425,
                30725.4485529926
            ]
        },
        'RCP-30-5A (Euroflow) Lot EAM02 & EAM01': {
            'MECSB': [480.0, 698.0, 1192.0, 2947.0, 6546.0, 15893.0, 27382.0],
            'MEBFP': [1295.0, 2398.0, 4884.0, 13920.0, 34027.0, 95282.0, 172500.0],
            'MEFL': [789.0, 1896.0, 4872.0, 15619.0, 47116.0, 143912.0, 333068.0],
            'MEPE': [507.0, 1204.0, 3171.0, 10440.0, 34385.0, 114122.0, 311207.0],
            'MEPTR': [187.0, 543.0, 1536.0, 5423.0, 17825.0, 63989.0, 207649.0],
            'MECY': [998.0, 3064.0, 8614.0, 28030.0, 90459.0, 298273.0, 849431.0],
            'MEPCY7': [106.0, 343.0, 1088.0, 4215.0, 15949.0, 62905.0, 208319.0],
            'MEAP': [736.0, 1892.0, 4804.0, 14248.0, 42425.0, 113026.0, 227044.0],
            'MEAXL700': [682.0, 1276.0, 2352.0, 4724.0, 9284.0, 17217.0, 26930.0],
            'MEAPCY7': [558.0, 1417.0, 3224.0, 8309.0, 20779.0, 48391.0, 89183.0]
        },
        'RCP-30-5A (Euroflow) Lot EAK01, EAG01, EAE01 & EAF01': {
            'MECSB': [
                3827.07306877147, 6410.85503814999, 12405.91715676,
                37097.3178176766, 92487.7710023634, 267142.304767532,
                499972.639106986
            ],
            'MEBFP': [
                2584.06901535744, 5291.27272439487, 11909.3205931143,
                38804.9157590269, 107470.790614424, 359515.748179449,
                736906.777253776
            ],
            'MEFL': [806.0, 2159.0, 5640.0, 19900.0, 52630.0, 172155.0, 345870.0],
            'MEPE': [409.0, 1250.0, 3428.0, 12229.0, 34294.0, 113118.0, 256134.0],
            'MEPTR': [171.0, 538.0, 1514.0, 5659.0, 16972.0, 64615.0, 183897.0],
            'MECY':
            [1276.0, 3603.0, 9520.0, 35518.0, 102755.0, 328185.0, 1052496.0],
            'MEPCY7': [
                9726.6114174626, 25173.4200339912, 57085.1373522142,
                136728.333019744, 324682.702797253
            ],
            'MEAP':
            [1366.0, 4706.0, 14822.0, 58161.0, 140920.0, 204810.0, 280646.0],
            'MEAXL700': [
                1180.89572037678, 3930.96580785077, 11270.6100091203,
                45502.2217551306, 109122.081384077, 151781.075700287,
                237988.013854553
            ],
            'MEAPCY7': [
                12540.2912310804, 27790.424415523, 57114.7530172427,
                137792.795419592, 245420.419831163, 312870.988997371,
                387104.388350457
            ]
        },
        'RCP-30-5A Lot AK01, AJ01, AH02, AH01, AF02, AF01, AD04 & AE01': {
            'MECSB': [216.0, 464.0, 1232.0, 2940.0, 7669.0, 19812.0, 35474.0],
            'MEBFP': [
                861.176890115253, 1997.18594899185, 5775.55800127844,
                15232.7589688612, 45388.9855190994, 152561.805143073,
                396759.154027137
            ],
            'MEFL': [792.0, 2079.0, 6588.0, 16471.0, 47497.0, 137049.0, 271647.0],
            'MEPE': [531.0, 1504.0, 4819.0, 12506.0, 36159.0, 109588.0, 250892.0],
            'MEPTR': [233.0, 669.0, 2179.0, 5929.0, 18219.0, 63944.0, 188785.0],
            'MECY':
            [1614.0, 4035.0, 12025.0, 31896.0, 95682.0, 353225.0, 1077421.0],
            'MEPCY7': [
                14916.4569850334, 42336.4964302585, 153840.442723689,
                494262.78101307
            ],
            'MEAP': [373.0, 1079.0, 3633.0, 9896.0, 28189.0, 79831.0, 151008.0],
            'MEAPCY7': [
                2863.86529976503, 7644.40047827793, 19081.4267726604,
                37257.7414357138
            ]
        },
        'RCP-30-5A Lot AG01': {
            'MECSB': [
                165.674334973794, 340.486972724961, 826.600919891466,
                2624.32033982357, 7136.97835687739, 19016.8923138331,
                32485.972305376
            ],
            'MEBFP': [
                783.479435075178, 1649.6663503655, 4198.58208277468,
                14660.9866605248, 45084.832628766, 155778.308324188,
                386263.847966924
            ],
            'MEFL': [646.0, 1704.0, 4827.0, 15991.0, 47609.0, 135896.0, 273006.0],
            'MEPE': [418.0, 1188.0, 3445.0, 11858.0, 35821.0, 108150.0, 248022.0],
            'MEPTR': [182.0, 512.0, 1503.0, 5542.0, 17662.0, 61847.0, 179707.0],
            'MECY':
            [1301.0, 3260.0, 8681.0, 30542.0, 94737.0, 355044.0, 1041442.0],
            'MEPCY7': [43612.1316610686, 157277.99967019, 471882.579572875],
            'MEAP': [292.0, 903.0, 2944.0, 10279.0, 31830.0, 88779.0, 136890.0],
            'MEAPCY7': [
                152.481010512631, 358.004365649928, 966.611772258365,
                2861.65093025875, 8041.50258137422, 21487.9458259072,
                34373.1492632902
            ]
        },
        'RCP-30-5A Lot AA01, AA02, AA03, AA04, AB01, AB02, AC01 & GAA01-R': {
            'MECSB': [179.0, 400.0, 993.0, 3203.0, 6083.0, 17777.0, 36331.0],
            'MEBFP': [700.0, 1705.0, 4262.0, 17546.0, 35669.0, 133387.0, 412089.0],
            'MEFL': [692.0, 2192.0, 6028.0, 17493.0, 35674.0, 126907.0, 290983.0],
            'MEPE': [505.0, 1777.0, 4974.0, 13118.0, 26757.0, 94930.0, 250470.0],
            'MEPTR': [207.0, 750.0, 2198.0, 6063.0, 12887.0, 51686.0, 170219.0],
            'MECY':
            [1437.0, 4693.0, 12901.0, 36837.0, 76621.0, 261671.0, 1069858.0],
            'MEPCY7': [32907.0, 107787.0, 503797.0],
            'MEAP': [578.0, 2433.0, 6720.0, 17962.0, 30866.0, 51704.0, 146080.0],
            'MEAPCY7': [718.0, 1920.0, 5133.0, 9324.0, 14210.0, 26735.0]
        },
        'RCP-30-5A Lot AC02, AC03 & AD01': {
            'MEPB': [
                179.490842861769, 399.130271822164, 1004.33041842402,
                3326.09220035309, 6280.9781554728, 18181.900886873,
                37446.4126347345
            ],
            'MEAmC': [
                689.818391446723, 1645.66379392412, 4353.99728581043,
                17956.9358902402, 37196.3751279619, 136964.361513719,
                422642.751819192
            ],
            'MEFL': [
                694.316757280561, 2095.54714141499, 6077.97998121964,
                18079.7185767491, 37488.3221945023, 127548.70589779,
                292408.003430039
            ],
            'MEPE': [
                525.988079665053, 1735.72870920068, 5023.48980798513,
                13251.1367386049, 27327.3892526052, 96552.680798141,
                259880.668965796
            ],
            'MEPTR': [
                218.12305864236, 737.206689077331, 2197.57129248996,
                6081.95974182049, 13048.0691337032, 52446.8891318169,
                177982.883907379
            ],
            'MECY': [
                1434.98342378079, 4725.12552939372, 12977.4579084514,
                34975.0986132135, 71893.2990690699, 258366.215367105,
                1120607.11147369
            ],
            'MEPCY7': [
                14858.8422415397, 31336.9778664833, 107223.701409309,
                519777.268051615
            ],
            'MEAP': [1184.0, 4024.0, 8892.0, 20919.0, 35336.0, 62371.0, 160356.0],
            'MEAPCY7': [
                1638.44517911143, 4232.87970031999, 8021.74368319802,
                14091.8060342384, 27002.3850136509
            ]
        },
        'RCP-30-5A Lot Z02 and Z03': {
            'MEFL': [601.0, 1645.0, 4920.0, 15169.0, 39664.0, 149723.0, 309976.0],
            'MEPE': [404.0, 1096.0, 3752.0, 11972.0, 29596.0, 126945.0, 292721.0],
            'MEPTR': [175.0, 480.0, 1687.0, 5549.0, 14005.0, 66220.0, 180787.0],
            'MECY':
            [1684.0, 3603.0, 10436.0, 29791.0, 70042.0, 310480.0, 830853.0],
            'MEAP': [6600.0, 11135.0, 20320.0, 68250.0, 134075.0]
        },
        'RCP-30-5 Lot AA01, AB01, AB02, AC01 & AD01': {
            'MEFL': [6028.0, 17493.0, 35674.0, 126907.0, 290983.0],
            'MEPE': [4974.0, 13118.0, 26757.0, 94930.0, 250470.0],
            'MEPTR': [2198.0, 6063.0, 12887.0, 51686.0, 170219.0],
            'MECY': [12901.0, 36837.0, 76621.0, 261671.0, 1069858.0],
            'MEAP': [6720.0, 17962.0, 30866.0, 51704.0, 146080.0]
        },
        'RCP-30-5 Lot AM02, AM01, AL01, AH01, AG01, AF01 & AD03': {
            'MEPB': [
                902.826150264251, 2543.25777035562, 7577.3103315121,
                19902.1552759773, 35490.1854343577
            ],
            'MEKO': [
                4100.1862606147, 13503.2020463521, 45019.6494865316,
                152691.355293162, 391037.895005993
            ],
            'MEFL': [4447.0, 14227.0, 46322.0, 133924.0, 276897.0],
            'MEPE': [3236.0, 10754.0, 34842.0, 104483.0, 245894.0],
            'METR': [1486.0, 5112.0, 17664.0, 60371.0, 179787.0],
            'MECY5.5': [8737.0, 28177.0, 93996.0, 334087.0, 1023447.0],
            'MEPCY7': [
                4447.52977431211, 12826.6344100731, 41676.365575392,
                149440.701418692, 474797.252391984
            ],
            'MEAP': [2395.0, 8273.0, 27652.0, 75669.0, 145428.0],
            'MEA700': [
                7850.64102564103, 26574.358974359, 87058.3333333333,
                232771.153846154, 428898.076923077
            ],
            'MEA750': [
                643.319414830418, 1682.85038466727, 4905.43254465399,
                15637.5278759487, 44664.1560269625
            ]
        },
        'RCP-60-5': {
            'MECSB': [
                751.643759068972, 1920.57650587408, 5279.84831730671,
                17646.2346728647, 46326.3118984758
            ],
            'MEBFP': [
                2864.0329353713, 8443.49646470612, 26220.2573429104,
                100989.554710812, 303460.407560259
            ],
            'MEFL': [
                4353.33008297943, 13939.3805748209, 43401.6051922607,
                159034.493056801, 359570.84295444
            ],
            'MEPE': [
                3177.87432453532, 9831.93042961122, 31667.5628810337,
                126234.183762106, 304230.63179907
            ],
            'MEPTR': [
                1249.10167677766, 4450.58520313724, 15543.94283828,
                67795.5145283527, 149369.723878365
            ],
            'MEPCY': [
                15.8150373621659, 5086.64305323489, 16533.7622690629,
                53254.5341431493, 213548.514439041, 535345.766430253
            ]
        },
        'URCP 38-2K': {
            'MEBV421': [211.0, 1267.0, 3519.0, 8917.0, 20718.0],
            'MEBV500': [1750.0, 6320.0, 13155.0, 28040.0, 52715.0],
            'MEBV605': [2300.0, 8685.0, 21000.0, 58960.0, 158765.0],
            'MECSB': [211.0, 1267.0, 3519.0, 8917.0, 20718.0],
            'MEBFP': [608.0, 4104.0, 11561.0, 30735.0, 72366.0],
            'MEFL': [3635.0, 31180.0, 93455.0, 237290.0, 437385.0],
            'MEPE': [2870.0, 23850.0, 67430.0, 163085.0, 319420.0],
            'MEPTR': [7480.0, 62600.0, 184935.0, 508840.0, 1149085.0],
            'MEPCY5': [630.0, 10900.0, 53125.0, 250350.0, 1109525.0],
            'MEPerCP': [6800.0, 34000.0, 85330.0, 216650.0, 534585.0],
            'MEPerCPCy5.5': [3115.0, 20615.0, 75070.0, 309220.0, 1272450.0],
            'MEPCY7': [16460.0, 62930.0, 289710.0, 1265380.0],
            'MEAP': [1400.0, 8400.0, 24000.0, 57000.0, 101500.0],
            'MEAlexa700': [7720.0, 65300.0, 210450.0, 563470.0, 1274350.0],
            'MEAPCY7': [1755.0, 13655.0, 43800.0, 117260.0, 257610.0]
        },
        'URCP 38-2K Lot AN01, AM01, AL02, AL01, AK03, AK02, AK01, AJ02 & AJ03': {
            'MEBV421': [543.0, 2418.0, 5646.0, 12601.0, 28608.0],
            'MEBV510': [1175.0, 5189.0, 12663.0, 30220.0, 72302.0],
            'MEBV605': [
                883.0, 3331.6464149406, 8126.37672213155, 21926.3325629935,
                63287.45416728
            ],
            'MEBV650': [
                3000.93657721926, 7266.96915687983, 20931.195845994,
                62364.6257039747
            ],
            'MEBV711': [
                706.371218651242, 2806.25617659897, 6536.3741423501,
                19293.0554727062, 56753.3744602146
            ],
            'MEBV786': [
                706.748702299005, 2758.23102388779, 6388.95396508851,
                19061.9810254142, 56137.0077072925
            ],
            'MEFL': [3884.0, 33300.0, 97805.0, 253325.0, 484433.0],
            'MEPerCPCy5.5': [
                603.044436159273, 2993.43100035362, 7241.2334144918,
                20027.1938003096, 54740.5383527368
            ],
            'MEPE': [
                3107.83774255919, 24809.3002510258, 70842.9661903017,
                181769.458300597, 347816.312804139
            ],
            'MEPTR': [6845.0, 59229.0, 175449.0, 487544.0, 1082135.0],
            'MEPCY5 (488 ex)': [1192.0, 15866.0, 62567.0, 299858.0, 1305867.0],
            'MEPCY5 (561 ex)':
            [15579.0, 258556.0, 1074152.0, 4387781.0, 13943895.0],
            'MEPCy5.5': [
                6371.10927410355, 31258.2726388408, 75288.3558534389,
                211044.540217265, 542552.430980202
            ],
            'MECY7': [14926.0, 53996.0, 282559.0, 1368162.0],
            'MEAP': [1224.0, 6275.0, 16016.0, 49490.0, 109302.0],
            'MEAlexa700': [
                6591.02998645881, 42548.5504851513, 125788.849777232,
                475002.69573088, 1269504.83599914
            ],
            'MEAPCY7': [1494.0, 9444.0, 27262.0, 101046.0, 258585.0],
            'MEBUV395': [
                871.141855176918, 3857.76891199076, 8428.28640168851,
                16978.9108417844, 29323.3959547754
            ],
            'MEBUV737': [
                183.259605936699, 785.83204702247, 2025.88773461442,
                7453.30284333274, 29429.229169638
            ]
        },
        'URCP 50-2K Lot AM01 & AJ01': {
            'MEBV421': [
                553.069779590127, 2688.24002627859, 6206.37168246614,
                15217.7386666591, 31977.7923579754
            ],
            'MEBV510': [
                1025.26689799175, 4383.09920065957, 15056.4249502571,
                38999.7688815165, 83332.4222376615
            ],
            'MEBV605': [
                709.488157879778, 3805.19098506487, 8979.50618284471,
                26351.2615487229, 45928.1493603154
            ],
            'MEBV650': [
                1019.75926894535, 5239.75611798151, 11479.5593728535,
                31915.4253433031, 70341.7021485763
            ],
            'MEBV711': [
                1354.17337049447, 7066.55939540903, 14960.9218266887,
                41313.9874398959, 100837.800463451
            ],
            'MEBV786': [
                706.748702299005, 2758.23102388779, 6388.95396508851,
                19061.9810254142, 56137.0077072925
            ],
            'MEFL': [
                2601.82488607447, 23545.8436109714, 59292.4242759641,
                165160.426302325, 331838.359003713
            ],
            'MEPerCPCy5.5': [
                1350.20092756121, 13792.2877652179, 40033.6068115353,
                171229.100849295, 659334.053913482
            ],
            'MEPE': [
                2106.44797555202, 17768.3884525601, 45248.196768689,
                123615.682766542, 234032.785605637
            ],
            'MEPTR': [
                1226.55300211598, 11850.2867438131, 30690.2606448733,
                86022.0614784648, 166798.756993696
            ],
            'MEPCY5 (488 ex)': [
                1144.7161092547, 15196.6416305133, 46123.587062421,
                171320.367389561, 452836.401230128
            ],
            'MEPCY5 (561 ex)': [
                1144.7161092547, 15196.6416305133, 46123.587062421,
                171320.367389561, 452836.401230128
            ],
            'MEPCy5.5': [
                11628.3996442711, 65451.0769345489, 142185.562107704,
                401557.948615379, 979320.213365762
            ],
            'MECY7': [
                1389.33665669744, 17806.9766820921, 57589.2401205632,
                292894.463825277, 1205021.89058945
            ],
            'MEAP': [
                11452.646449399, 84842.0267436591, 203505.318422001,
                604708.533266664, 1290472.19989895
            ],
            'MEAlexa700': [
                20616.5600284507, 185848.147292231, 486731.646398276,
                1702570.50723759, 4437433.03758529
            ],
            'MEAPCY7': [
                2537.13182116939, 22526.7252158067, 58567.0220162963,
                202718.67988687, 521885.134400135
            ]
        },
        'URCP 50-2K': {
            'MEFL': [2615.0, 22590.0, 63305.0, 155800.0, 328880.0],
            'MEPE': [2205.0, 19085.0, 54450.0, 134910.0, 248895.0],
            'MEPTR': [1390.0, 12155.0, 35370.0, 92185.0, 199280.0],
            'MEPerCP': [1840.0, 16485.0, 54070.0, 195200.0, 1074110.0],
            'MEPCY5': [1270.0, 11790.0, 37800.0, 127280.0, 618430.0],
            'MEPerCPCy5.5': [1280.0, 11675.0, 37440.0, 127460.0, 623165.0],
            'MEPCY7': [1555.0, 10910.0, 37500.0, 149310.0, 1060350.0],
            'MEAP': [6780.0, 56850.0, 160850.0, 403930.0, 919070.0],
            'MEAPCY7': [1480.0, 13305.0, 38640.0, 106285.0, 417030.0]
        }
    }
    """
    A dictionary containing the calibrated beads that Cytoflow currently knows
    about.  The available bead sets are:

    - Spherotech ACP 30-2K
    - Spherotech RCP-30-5A Lot AN04, AN03, AN02, AN01, AM02, AM01, AL01, AK04, AK03 & AK02**
    - Spherotech RCP-30-5A (Euroflow) Lot EAM02 & EAM01
    - Sphreotech RCP-30-5A (Euroflow) Lot EAK01, EAG01, EAE01 & EAF01
    - Spherotech RCP-30-5A Lot AK01, AJ01, AH02, AH01, AF02, AF01, AD04 & AE01
    - Spherotech RCP-30-5A Lot AG01
    - Spherotech RCP-30-5A Lot AA01, AA02, AA03, AA04, AB01, AB02, AC01 & GAA01-R
    - Spherotech RCP-30-5A Lot AC02, AC03 & AD01
    - Spherotech RCP-30-5A Lot Z02 and Z03
    - Spherotech RCP-30-5 Lot AA01, AB01, AB02, AC01 & AD01
    - Spherotech RCP-30-5 Lot AM02, AM01, AL01, AH01, AG01, AF01 & AD03
    - Spherotech RCP-60-5
    - Spherotech URCP 38-2K
    - Spherotech URCP 38-2K Lot AN01, AM01, AL02, AL01, AK03, AK02, AK01, AJ02 & AJ03
    - Spherotech URCP 50-2K Lot AM01 & AJ01
    - Spherotech URCP 50-2K
    
    The Spherotech fluorophores labels and the laser / filter sets 
    (that I know about) are:
    
    - **MECSB** (Cascade Blue, 405 --> 450/50)
    - **MEBFP** (BFP, 405 --> 530/40)
    - **MEFL** (Fluroscein, 488 --> 530/40)
    - **MEPE** (Phycoerythrin, 488 --> 575/25)
    - **MEPTR** (PE-Texas Red, 488 --> 613/20)
    - **MECY** (Cy5, 488 --> 680/30)
    - **MEPCY7** (PE-Cy7, 488 --> 750 LP)
    - **MEAP** (APC, 633 --> 665/20)
    - **MEAPCY7** (APC-Cy7, 635 --> 750 LP)

    """

@provides(cytoflow.views.IView)
class BeadCalibrationDiagnostic(HasStrictTraits):
    """
    A diagnostic view for `BeadCalibrationOp`.
        
    Plots the smoothed histogram of the bead data; the peak locations;
    a scatter plot of the raw bead fluorescence values vs the calibrated unit 
    values; and a line plot of the model that was computed.  Make sure that the
    relationship is linear; if it's not, it likely isn't a good calibration!
    
    Attributes
    ----------
    op : Instance(`BeadCalibrationOp`)
        The operation instance whose parameters we're plotting.  Set 
        automatically if you created the instance using 
        `BeadCalibrationOp.default_view`.

    """
    
    # traits   
    id = Constant("edu.mit.synbio.cytoflow.view.beadcalibrationdiagnosticview")
    friendly_id = Constant("Bead Calibration Diagnostic")
        
    op = Instance(BeadCalibrationOp)
    
    def plot(self, experiment):
        """
        Plots the diagnostic view.
        
        Parameters
        ----------
        experiment : `Experiment`
            The experiment used to create the diagnostic plot.
        
        """

        if experiment is None:
            raise util.CytoflowViewError('experiment', "No experiment specified")

        channels = list(self.op.units.keys())

        if not channels:
            raise util.CytoflowViewError(None, "No channels to plot")

        if set(channels) != set(self.op._histograms.keys()):
            raise util.CytoflowViewError(None, "You must estimate the parameters "
                                               "before plotting")

        plt.figure()
        
        for idx, channel in enumerate(channels):            
            _, hist_bins, hist_smooth = self.op._histograms[channel]
                
            plt.subplot(len(channels), 2, 2 * idx + 1)
            plt.xscale('log')
            plt.xlabel(channel)
            plt.plot(hist_bins[1:], hist_smooth)
            
            plt.axvline(self.op.bead_brightness_threshold, color = 'blue', linestyle = '--' )
            if self.op.bead_brightness_cutoff:
                plt.axvline(self.op.bead_brightness_cutoff, color = 'blue', linestyle = '--' )
            else:
                plt.axvline(experiment.metadata[channel]['range'] * 0.7, color = 'blue', linestyle = '--')                

            if channel in self.op._peaks:
                for peak in self.op._peaks[channel]:
                    plt.axvline(peak, color = 'r')
                    
            if channel in self.op._peaks and channel in self.op._mefs:
                plt.subplot(len(channels), 2, 2 * idx + 2)
                plt.xscale('log')
                plt.yscale('log')
                plt.xlabel(channel)
                plt.ylabel(self.op.units[channel])
                plt.plot(self.op._peaks[channel], 
                         self.op._mefs[channel], 
                         marker = 'o')
                
                xmin, xmax = plt.xlim()
                x = np.logspace(np.log10(xmin), np.log10(xmax))
                plt.plot(x, 
                         self.op._calibration_functions[channel](x), 
                         color = 'r', linestyle = ':')
            
        plt.tight_layout(pad = 0.8)
            

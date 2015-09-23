# make sure pandas is new enough
from pandas.version import version as _pd_version
from distutils.version import LooseVersion

if LooseVersion(_pd_version) < '0.15.0':
    raise ImportError('cytoflow needs pandas >= 0.15.0.  trust me.')

# make sure numexpr is around.

from numexpr import version as _numexpr_version

if LooseVersion(_numexpr_version.version) < '2.1':
    raise ImportError('cytoflow needs numexpr >= 2.1')

from experiment import Experiment
from operations.threshold import ThresholdOp
from operations.range import RangeOp
from operations.range2d import Range2DOp
from operations.polygon import PolygonOp
from operations.hlog import HlogTransformOp
from operations.logicle import LogicleTransformOp
from operations.log import LogTransformOp
from operations.import_op import ImportOp, Tube
from operations.autofluorescence import AutofluorescenceOp
from operations.bleedthrough_piecewise import BleedthroughPiecewiseOp
from operations.bead_calibration import BeadCalibrationOp
from operations.color_translation import ColorTranslationOp
from operations.binning import BinningOp

from views.histogram import HistogramView
from views.hexbin import HexbinView
from views.scatterplot import ScatterplotView
from views.range_selection import RangeSelection
from views.range_selection_2d import RangeSelection2D
from views.threshold_selection import ThresholdSelection
from views.poly_selection import PolygonSelection
from views.stats_1d import Stats1DView
from views.stats_2d import Stats2DView
from views.bar_chart import BarChartView

from utility.util import geom_mean

__version__ = "0.1.4"
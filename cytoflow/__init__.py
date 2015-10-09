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
from views.threshold_selection import ThresholdSelection
from views.stats_1d import Stats1DView
from views.stats_2d import Stats2DView
from views.bar_chart import BarChartView

from utility.util import geom_mean

__version__ = "0.1.8"
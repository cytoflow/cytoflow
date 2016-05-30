#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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

from __future__ import absolute_import

# suppress a meaningless warning from seaborn
import warnings
warnings.filterwarnings('ignore', '.*IPython widgets are experimental.*')

# basics
from .experiment import Experiment
from .operations.import_op import ImportOp, Tube

# gates
from .operations.threshold import ThresholdOp
from .operations.range import RangeOp
from .operations.range2d import Range2DOp
from .operations.polygon import PolygonOp
from .operations.quad import QuadOp

# transforms (deprecated!)
from .operations.hlog import HlogTransformOp
from .operations.logicle import LogicleTransformOp
from .operations.log import LogTransformOp

# TASBE
from .operations.autofluorescence import AutofluorescenceOp
from .operations.bleedthrough_piecewise import BleedthroughPiecewiseOp
from .operations.bead_calibration import BeadCalibrationOp
from .operations.color_translation import ColorTranslationOp

# data-driven
from .operations.gaussian_1d import GaussianMixture1DOp
from .operations.gaussian_2d import GaussianMixture2DOp

# misc
from .operations.binning import BinningOp
from .operations.bleedthrough_linear import BleedthroughLinearOp

# views
from .views.histogram import HistogramView
from .views.scatterplot import ScatterplotView
from .views.stats_1d import Stats1DView
from .views.stats_2d import Stats2DView
from .views.bar_chart import BarChartView

from .views.kde_1d import Kde1DView
from .views.kde_2d import Kde2DView

from .views.histogram_2d import Histogram2DView
from .views.violin import ViolinPlotView
from .views.table import TableView

# util
from cytoflow.utility.util_functions import geom_mean
from cytoflow.utility.scale import set_default_scale

__version__ = "0.3.0"

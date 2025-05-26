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
cytoflow
--------

``cytoflow`` is a package for quantitative, reproducible analysis of flow 
cytometry data.  

Written by Brian Teague, bpteague@gmail.com

Copyright Massachusetts Institute of Technology 2015-2018

Copyright Brian Teague 2018-2025
"""

# check python version
import sys
if sys.version_info < (3, 4):
    raise Exception("Cytoflow requires Python 3.4 or later")

# suppress meaningless warnings from seaborn and sklearn
import warnings
warnings.filterwarnings('ignore', '.*IPython widgets are experimental.*')
warnings.filterwarnings('ignore', 'axes.color_cycle is deprecated and replaced with axes.prop_cycle')
warnings.filterwarnings('ignore', 'X has feature names, but NearestNeighbors was fitted without feature names')

# and matplotlib 3.1.1 -- there's some weird interaction with seaborn here.
import matplotlib.text
import logging

        
from cytoflow.utility.logging_ext import MplFilter
matplotlib.text._log.addFilter(MplFilter())  # @UndefinedVariable

# keep track of whether we're running in the GUI.
# there is the occasional place where we differ in behavior
RUNNING_IN_GUI = False

# basics
from .experiment import Experiment
from .operations.import_op import ImportOp, Tube

# gates
from .operations.threshold import ThresholdOp
from .operations.range import RangeOp
from .operations.range2d import Range2DOp
from .operations.polygon import PolygonOp
from .operations.quad import QuadOp

# TASBE
from .operations.autofluorescence import AutofluorescenceOp
from .operations.bleedthrough_linear import BleedthroughLinearOp
from .operations.bead_calibration import BeadCalibrationOp
from .operations.color_translation import ColorTranslationOp

# data-driven
from .operations.ratio import RatioOp
from .operations.density import DensityGateOp
from .operations.gaussian import GaussianMixtureOp
from .operations.kmeans import KMeansOp
from .operations.flowpeaks import FlowPeaksOp
from .operations.pca import PCAOp
from .operations.tsne import tSNEOp
from .operations.som import SOMOp

# channels
from .operations.channel_stat import ChannelStatisticOp
from .operations.frame_stat import FrameStatisticOp
from .operations.xform_stat import TransformStatisticOp

# misc
from .operations.binning import BinningOp
from .operations.flowclean import FlowCleanOp

# views
from .views.histogram import HistogramView
from .views.scatterplot import ScatterplotView
from .views.densityplot import DensityView
from .views.stats_1d import Stats1DView
from .views.stats_2d import Stats2DView
from .views.bar_chart import BarChartView
from .views.matrix import MatrixView

from .views.kde_1d import Kde1DView
from .views.kde_2d import Kde2DView

from .views.histogram_2d import Histogram2DView
from .views.violin import ViolinPlotView
from .views.table import TableView
from .views.long_table import LongTableView
from .views.radviz import RadvizView
from .views.parallel_coords import ParallelCoordinatesView

from .views.export_fcs import ExportFCS

# util
from .utility.util_functions import (geom_mean, geom_sd, geom_sem)
from .utility.algorithms import (ci, percentiles)
from .utility.scale import set_default_scale, get_default_scale


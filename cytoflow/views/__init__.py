#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
cytoflow.views
--------------

This package contains all `cytoflow` views -- classes
implementing `IView` whose ``plot()`` function plots an
experiment.
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns

# set seaborn defaults.  this is mostly for the Jupyter notebook;
# these settings can be overridden in the GUI
sns.set(context = "paper", style = "whitegrid", 
        rc = {"xtick.bottom": True, "ytick.left": True})

from .i_view import IView
from .i_selectionview import ISelectionView

from .base_views import Base1DView, Base2DView

from .bar_chart import BarChartView
from .histogram import HistogramView
from .scatterplot import ScatterplotView
from .densityplot import DensityView
from .stats_1d import Stats1DView
from .stats_2d import Stats2DView
from .kde_1d import Kde1DView
from .kde_2d import Kde2DView
from .histogram_2d import Histogram2DView
from .violin import ViolinPlotView
from .table import TableView
from .radviz import RadvizView
from .parallel_coords import ParallelCoordinatesView
from .export_fcs import ExportFCS
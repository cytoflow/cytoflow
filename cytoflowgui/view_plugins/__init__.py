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

from .i_view_plugin import IViewPlugin, VIEW_PLUGIN_EXT
from .view_plugin_base import ViewHandler
from .histogram import HistogramPlugin
from .histogram_2d import Histogram2DPlugin
from .density import DensityPlugin
from .scatterplot import ScatterplotPlugin
from .bar_chart import BarChartPlugin
from .stats_1d import Stats1DPlugin
from .stats_2d import Stats2DPlugin
from .kde_1d import Kde1DPlugin
from .kde_2d import Kde2DPlugin
from .violin import ViolinPlotPlugin
from .table import TablePlugin
from .parallel_coords import ParallelCoordinatesPlugin
from .radviz import RadvizPlugin
from .export_fcs import ExportFCSPlugin
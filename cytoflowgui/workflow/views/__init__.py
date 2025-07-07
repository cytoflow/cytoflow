#!/usr/bin/env python3.8

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
cytoflowgui.workflow.views
--------------------------

"""
from .view_base import IWorkflowView, WorkflowView, WorkflowByView, WorkflowFacetView, Channel

from .bar_chart import BarChartWorkflowView, BarChartPlotParams
from .density import DensityWorkflowView, DensityPlotParams
from .histogram_2d import Histogram2DWorkflowView, Histogram2DPlotParams
from .histogram import HistogramWorkflowView, HistogramPlotParams
from .kde_1d import Kde1DWorkflowView, Kde1DPlotParams
from .kde_2d import Kde2DWorkflowView, Kde2DPlotParams
from .parallel_coords import ParallelCoordinatesWorkflowView, ParallelCoordinatesPlotParams, Channel as ParallelCoordinatesChannel
from .radviz import RadvizWorkflowView, RadvizPlotParams, Channel as RadvizChannel
from .scatterplot import ScatterplotWorkflowView, ScatterplotPlotParams
from .stats_1d import Stats1DWorkflowView, Stats1DPlotParams
from .stats_2d import Stats2DWorkflowView, Stats2DPlotParams
from .table import TableWorkflowView
from .long_table import LongTableWorkflowView
from .violin import ViolinPlotWorkflowView, ViolinPlotParams
from .export_fcs import ExportFCSWorkflowView
from .matrix import MatrixWorkflowView, MatrixPlotParams
from .mst import MSTWorkflowView, MSTPlotParams


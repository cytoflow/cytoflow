
from .view_base import IWorkflowView, WorkflowView, Channel

from .bar_chart import BarChartWorkflowView, BarChartPlotParams
from .density import DensityWorkflowView, DensityPlotParams
from .histogram_2d import Histogram2DWorkflowView, Histogram2DPlotParams
from .histogram import HistogramWorkflowView, HistogramPlotParams
from .kde_1d import Kde1DWorkflowView, Kde1DPlotParams
from .kde_2d import Kde2DWorkflowView, Kde2DPlotParams
from .parallel_coords import ParallelCoordinatesWorkflowView, ParallelCoordinatesPlotParams
from .radviz import RadvizWorkflowView, RadvizPlotParams
from .scatterplot import ScatterplotWorkflowView, ScatterplotPlotParams
from .stats_1d import Stats1DWorkflowView, Stats1DPlotParams
from .stats_2d import Stats2DWorkflowView, Stats2DPlotParams
from .table import TableWorkflowView
from .violin import ViolinPlotWorkflowView, ViolinPlotParams


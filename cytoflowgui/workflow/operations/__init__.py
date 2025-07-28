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
cytoflowgui.workflow.operations
-------------------------------
"""

from .operation_base import IWorkflowOperation
from .import_op import ImportWorkflowOp, Channel as ImportChannel

from .threshold import ThresholdWorkflowOp, ThresholdSelectionView
from .quad import QuadWorkflowOp, QuadSelectionView
from .range import RangeWorkflowOp, RangeSelectionView
from .range2d import Range2DWorkflowOp, Range2DSelectionView, Range2DPlotParams
from .polygon import PolygonWorkflowOp, PolygonSelectionView, PolygonPlotParams

from .channel_stat import ChannelStatisticWorkflowOp
from .multi_channel_stat import MultiChannelStatisticWorkflowOp, Function as MultiChannelStatisticFunction
from .xform_stat import TransformStatisticWorkflowOp
from .merge_stat import MergeStatisticsWorkflowOp
from .ratio import RatioWorkflowOp

from .binning import BinningWorkflowOp, BinningWorkflowView
from .gaussian_1d import GaussianMixture1DWorkflowOp, GaussianMixture1DWorkflowView
from .gaussian_2d import GaussianMixture2DWorkflowOp, GaussianMixture2DWorkflowView
from .density import DensityGateWorkflowOp, DensityGateWorkflowView
from .kmeans import KMeansWorkflowOp, KMeansWorkflowView
from .flowpeaks import FlowPeaksWorkflowOp, FlowPeaksWorkflowView
from .pca import PCAWorkflowOp, Channel as PCAChannel
from .flowclean import FlowCleanWorkflowOp, Channel as FlowCleanChannel, FlowCleanWorkflowView
from .tsne import tSNEWorkflowOp, Channel as tSNEChannel
from .mst import MSTWorkflowOp, MSTWorkflowSelectionView
from .register import RegistrationWorkflowOp, Channel as RegistrationChannel, RegistrationDiagnosticWorkflowView

from .autofluorescence import AutofluorescenceWorkflowOp, AutofluorescenceWorkflowView
from .bead_calibration import BeadCalibrationWorkflowOp, BeadCalibrationWorkflowView, Unit as BeadCalibrationUnit
from .bleedthrough_linear import BleedthroughLinearWorkflowOp, BleedthroughLinearWorkflowView, Channel as BleedthroughChannel, Spillover as BleedthroughSpillover
from .color_translation import ColorTranslationWorkflowOp, ColorTranslationWorkflowView, Control as ColorTranslationControl
from .tasbe import TasbeWorkflowOp, TasbeWorkflowView
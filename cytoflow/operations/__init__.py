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
cytoflow.operations
-------------------

This package contains all :mod:`cytoflow` operations -- classes
implementing `IOperation` whose `IOperation.apply` function takes an 
`Experiment` and returns an `Experiment`.  
"""

from .i_operation import IOperation
from .import_op import ImportOp
from .external_label import ExternalLabelOp
 
# gates
from .threshold import ThresholdOp
from .range import RangeOp
from .range2d import Range2DOp
from .polygon import PolygonOp
from .quad import QuadOp

# data-driven
from .ratio import RatioOp
from .density import DensityGateOp
from .gaussian import GaussianMixtureOp
from .kmeans import KMeansOp
from .flowpeaks import FlowPeaksOp
from .pca import PCAOp

# statistics
from .channel_stat import ChannelStatisticOp
from .frame_stat import FrameStatisticOp
from .xform_stat import TransformStatisticOp
 
# TASBE
from .autofluorescence import AutofluorescenceOp
from .bleedthrough_linear import BleedthroughLinearOp
from .bead_calibration import BeadCalibrationOp
from .color_translation import ColorTranslationOp

# etc 
from .binning import BinningOp

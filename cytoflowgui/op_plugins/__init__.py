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
cytoflowgui.op_plugins
----------------------

`envisage.plugin.Plugin` classes and GUI `traitsui.handler.Controller` classes
to adapt modules from `cytoflowgui.workflow.operations` to the Qt / `traitsui` GUI.

The module docstrings are also the ones that are used for the GUI help
panel.
"""

from .i_op_plugin import IOperationPlugin, OpPluginManager, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler
from .import_op import ImportPlugin
# 
# # gates
from .threshold import ThresholdPlugin
from .range import RangePlugin
from .range2d import Range2DPlugin
from .polygon import PolygonPlugin
from .quad import QuadPlugin

# statistics and transformations
from .channel_stat import ChannelStatisticPlugin
from .multi_channel_stat import MultiChannelStatisticPlugin
from .xform_stat import TransformStatisticPlugin
from .merge_stat import MergeStatisticsPlugin
from .ratio import RatioPlugin

# # data-driven
from .binning import BinningPlugin
from .gaussian_1d import GaussianMixture1DPlugin
from .gaussian_2d import GaussianMixture2DPlugin
from .density import DensityGatePlugin
from .flowpeaks import FlowPeaksPlugin
from .kmeans import KMeansPlugin
from .pca import PCAPlugin
from .flowclean import FlowCleanPlugin
from .tsne import tSNEPlugin
from .som import SOMPlugin
from .mst import MSTPlugin
from .register import RegistrationPlugin

# tasbe
from .bleedthrough_linear import BleedthroughLinearPlugin
from .bead_calibration import BeadCalibrationPlugin
from .autofluorescence import AutofluorescencePlugin
from .color_translation import ColorTranslationPlugin
from .tasbe import TasbePlugin


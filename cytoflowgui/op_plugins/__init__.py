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

from i_op_plugin import (IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, 
                         shared_op_traits)
from import_op import ImportPlugin

# gates
from threshold import ThresholdPlugin
from range import RangePlugin
from range2d import Range2DPlugin
from polygon import PolygonPlugin

# transforms 
from log import LogPlugin
from hlog import HLogPlugin
from logicle import LogiclePlugin

# etc
from binning import BinningPlugin
from gaussian_1d import GaussianMixture1DPlugin
from gaussian_2d import GaussianMixture2DPlugin

# tasbe
from bleedthrough_linear import BleedthroughLinearPlugin
from bleedthrough_piecewise import BleedthroughPiecewisePlugin
from bead_calibration import BeadCalibrationPlugin
from autofluorescence import AutofluorescencePlugin
from color_translation import ColorTranslationPlugin
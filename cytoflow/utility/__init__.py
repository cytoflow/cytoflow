#!/usr/bin/env python2.7
# coding: latin-1

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

from .util_functions import (cartesian, iqr, geom_mean, geom_sd, geom_sd_range,
                             geom_sem, geom_sem_range, num_hist_bins, sanitize_identifier, 
                             categorical_order, random_string, is_numeric)
from .algorithms import ci
from .cytoflow_errors import CytoflowError, CytoflowOpError, CytoflowViewError
from .cytoflow_errors import CytoflowWarning, CytoflowOpWarning, CytoflowViewWarning

from .scale import scale_factory, IScale
from .custom_traits import PositiveInt, PositiveFloat, ScaleEnum, Deprecated, Removed

from .matplotlib_widgets import PolygonSelector
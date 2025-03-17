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
cytoflow.utility
----------------

This package contains a bunch of utility functions to support the other modules
in `cytoflow`. This includes numeric functions, algorithms, error handling, 
custom traits, custom `matplotlib` widgets, custom `matplotlib` scales, and
docstring handling.
"""

from .util_functions import (cartesian, iqr, geom_mean, geom_sd, geom_sd_range,
                             geom_sem, geom_sem_range, num_hist_bins, sanitize_identifier, 
                             random_string, is_numeric, cov2corr)

from .algorithms import ci, polygon_contains
from .cytoflow_errors import CytoflowError, CytoflowOpError, CytoflowViewError
from .cytoflow_errors import CytoflowWarning, CytoflowOpWarning, CytoflowViewWarning

from .scale import scale_factory, IScale, set_default_scale, get_default_scale
from .custom_traits import (PositiveInt, PositiveCInt, PositiveFloat, 
                            PositiveCFloat, ScaleEnum, Deprecated, Removed,
                            FloatOrNone, CFloatOrNone, IntOrNone, CIntOrNone,
                            UnitFloat)

from .docstring import expand_class_attributes, expand_method_parameters

from .fcswrite import write_fcs

from pandas.core.dtypes.inference import is_list_like
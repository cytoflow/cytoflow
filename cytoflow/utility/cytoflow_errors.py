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

"""
Created on Mar 5, 2015

@author: brian
"""
from __future__ import division, absolute_import
from exceptions import UserWarning

class CytoflowError(RuntimeError):
    pass

class CytoflowOpError(CytoflowError):
    pass

class CytoflowViewError(CytoflowError):
    pass

class CytoflowWarning(UserWarning):
    pass

class CytoflowOpWarning(CytoflowWarning):
    pass

class CytoflowViewWarning(CytoflowWarning):
    pass

# make sure these warnings show up all the time, instead of just once.

import warnings
warnings.simplefilter('always', CytoflowWarning)
warnings.simplefilter('always', CytoflowOpWarning)
warnings.simplefilter('always', CytoflowViewWarning)

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

"""
cytoflow.utility.cytoflow_errors
--------------------------------

Custom errors for `cytoflow`.  Allows for custom handling in the GUI.

`CytoflowError` -- a general error

`CytoflowOpError` -- an error raised by an operation

`CytoflowViewError` -- an error raised by a view

`CytoflowWarning` -- a general warning

`CytoflowOpWarning` -- a warning raised by an operation

`CytoflowViewWarning` -- a warning raised by a view
"""

import warnings

# Force warnings.warn() to omit the source code line in the message
formatwarning_orig = warnings.formatwarning
warnings.formatwarning = lambda message, category, filename, lineno, line=None: \
    formatwarning_orig(message, category, filename, lineno, line='')

class CytoflowError(RuntimeError):
    """
    A general error
    """

class CytoflowOpError(CytoflowError):
    """
    An error raised by an operation.  
    
    Parameters
    ----------
    args[0] : string
        The attribute or parameter whose bad value caused the error, or ``None``
        if there isn't one.
        
    args[1] : string
        A more verbose error message.
    """

class CytoflowViewError(CytoflowError):
    """
    An error raised by a view.  
    
    Parameters
    ----------
    args[0] : string
        The attribute or parameter whose bad value caused the error, or ``None``
        if there isn't one.
        
    args[1] : string
        A more verbose error message.
    """

class CytoflowWarning(UserWarning):
    """
    A general warning.
    """

class CytoflowOpWarning(CytoflowWarning):
    """
    A warning raised by an operation.
    
    Parameters
    ----------
    args[0] : string
        A verbose warning message
    """

class CytoflowViewWarning(CytoflowWarning):
    """
    A warning raised by a view.
    
    Parameters
    ----------
    args[0] : string
        A verbose warning message
    """

# make sure these warnings show up all the time, instead of just once.

warnings.simplefilter('always', CytoflowWarning)
warnings.simplefilter('always', CytoflowOpWarning)
warnings.simplefilter('always', CytoflowViewWarning)

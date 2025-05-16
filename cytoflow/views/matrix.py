#!/usr/bin/env python3.11
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2025
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
cytoflow.views.matrix
---------------------
"""

from traits.api import provides
from .i_view import IView
from .base_views import BaseStatisticsView

@provides(IView)
class MatrixView(BaseStatisticsView):
    """
    A view that creates a matrix view (a 2D grid representation) of a statistic. 
    Set `statistic` to the name of the statistic to plot; set `feature` to the name
    of that statistic's feature you'd like to analyze.
    
    Setting `xfacet` and `yfacet` to levels of the statistic's index will result in
    a separate column or row for each value of that statistic.
    
    There are three different ways of plotting the values of the matrix view 
    (the "cells" in the matrix.) 
    
    * If you leave `variable` set to ``None``, a "traditional" heat map is produced, 
      where each "cell" is a circle and the color of the circle is related to the 
      intensity of the value of `feature`.
      
    * Setting `variable` to a variable of the statistic and `type` to **pie** will
      draw a pie plot in each cell. The values in the `huefacet` are used as the
      categories of the pie, and the arc length of each slice of pie is related 
      to the intensity of the value of `feature`.
      
    * Setting `variable` to a variable of the statistic and `type` to **petal** will
      draw a "petal plot" in each cell. The values of the index level form the 
      categories, but unlike a pie plot, the arc width of each slice remains 
      equal. Instead, the radius of the pie slice scales with the square root 
      of the intensity, so that the relationship between area and intensity 
      remains the same.
      
    Optionally, you can set `size_feature` to scale the circles (or pies or petals)
    by another feature of the statistic. (Often used to scale by the count of a particular
    population or subset.)
    """


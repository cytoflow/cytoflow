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
cytoflow.views.petal
--------------------

A statistics view that plots a "petal plot" view of a statistic. A petal plot is
kind of like a pie plot, except that instead of the arc length of as segment
being proportional to a feature, the arc lengths of the segments are all the 
same and the radii vary according to a feature.

There are two different ways to lay out the petal plots. If either `xfacet`
or `yfacet` are set, the petal plots will be laid out in a grid
according to these facets. (If you just want a row or a column, set
only one of `xfacet` or `yfacet`; if you want just a single plot, don't
set either.)

Alternately, if `mst_facet` is set, the plot will be laid out using a
minumum spanning tree. Each unique value of the facet will get a node in the
tree. You must also specify the feature(s) containing the location of each
node using the `mst_locations` attribute.


"""
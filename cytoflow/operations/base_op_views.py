#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

'''
Created on Jul 30, 2017

@author: brian
'''

from traits.api import (provides, Instance, Property, List, DelegatesTo)
import matplotlib.pyplot as plt

from warnings import warn

import cytoflow.utility as util

from .i_operation import IOperation
from cytoflow.views import IView
from cytoflow.views.base_views import BaseView, Base1DView, Base2DView

@provides(IView)
class BaseOpView(BaseView):

    op = Instance(IOperation)
    facets = Property(List)
    by = Property(List)
    
    def _get_facets(self):
        return [self.xfacet, self.yfacet, self.huefacet]
    
    def _get_by(self):
        return list(set(self.op.by) - set(self.facets))
        
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to "plot".
        """
        
        for facet in self.facets:
            if facet and facet not in experiment.conditions:        
                raise util.CytoflowViewError("Facet {} not in the experiment"
                                            .format(facet))
            
            if facet and facet not in self.op.by:
                raise util.CytoflowViewError("Facet {} must be in the parent's by list, which is {}"
                                             .format(facet, self.op.by))
            
        for b in self.op.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {} not found"
                                      " in the experiment"
                                      .format(b))
        
        class plot_enum(object):
            
            def __init__(self, view, experiment):
                self._iter = None
                self._returned = False
                
                if view.by:
                    self._iter = experiment.data.groupby(view.by).__iter__()
                
            def __iter__(self):
                return self
            
            def __next__(self):
                if self._iter:
                    return next(self._iter)[0]
                else:
                    if self._returned:
                        raise StopIteration
                    else:
                        self._returned = True
                        return None
            
        return plot_enum(self, experiment)
    
    def plot(self, experiment, plot_name = None, **kwargs):

        experiment = experiment.clone()
        
        # try to apply the current operation
        try:
            experiment = self.op.apply(experiment)
        except util.CytoflowOpError:
            pass  
        
        # if apply() succeeded (or wasn't needed), set up the hue facet
        if self.op.name and self.op.name in experiment.conditions:
            if self.huefacet and self.huefacet != self.op.name:
                warn("Resetting huefacet to the model component (was {}, now {})."
                     .format(self.huefacet, self.op.name))
            self.huefacet = self.op.name
        else:
            self.huefacet = ""
        
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
                experiment.data.reset_index(drop = True, inplace = True)
            except Exception as e:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset)) from e
                
            if len(experiment) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))   
                
        # see if we're making subplots
        if self.by and plot_name is None:
            raise util.CytoflowViewError("You must use facets {} in either the "
                                         "plot variables or the plt name. "
                                         "Possible plot names: {}"
                                         .format(self.by, [x for x in self.enum_plots(experiment)]))
                                        
        if plot_name is not None:
            if plot_name is not None and not self.by:
                raise util.CytoflowViewError("Plot {} not from plot_enum"
                                             .format(plot_name))
                               
            groupby = experiment.data.groupby(self.by)

            if plot_name not in set(groupby.groups.keys()):
                raise util.CytoflowViewError("Plot {} not from plot_enum"
                                             .format(plot_name))
                
            experiment.data = groupby.get_group(plot_name)
            experiment.data.reset_index(drop = True, inplace = True)
            
        super().plot(experiment, **kwargs)
            
        if self.by and plot_name is not None:
            plt.title("{0} = {1}".format(self.by, plot_name))
    
@provides(IView)
class BaseOp1DView(BaseOpView, Base1DView):
    channel = DelegatesTo('op')
    scale = DelegatesTo('op')

@provides(IView)
class BaseOp2DView(BaseOpView, Base2DView):
    xchannel = DelegatesTo('op')
    xscale = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    yscale = DelegatesTo('op')



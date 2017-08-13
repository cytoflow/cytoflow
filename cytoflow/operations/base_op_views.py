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

from warnings import warn

from traits.api import (provides, Instance, Property, List, DelegatesTo)

import cytoflow.utility as util

from .i_operation import IOperation
from cytoflow.views import IView
from cytoflow.views.base_views import BaseView, BaseDataView, Base1DView, Base2DView

@provides(IView)
class OpView(BaseView):
    op = Instance(IOperation)
    
@provides(IView)
class Op1DView(OpView, Base1DView):
    channel = DelegatesTo('op')
    scale = DelegatesTo('op')
    
@provides(IView)
class Op2DView(OpView, Base2DView):
    xchannel = DelegatesTo('op')
    xscale = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    yscale = DelegatesTo('op')

@provides(IView)
class ByView(OpView):

    facets = Property(List)
    by = Property(List)
    
    def _get_facets(self):
        return [x for x in [self.xfacet, self.yfacet, self.huefacet] if x]   
    
    def _get_by(self):
        if self.op.by:
            return self.op.by
        else:
            return []
        
    def enum_plots(self, experiment):
        """
        Returns an iterator over the possible plots that this View can
        produce.  The values returned can be passed to "plot".
        """
                
        if len(self.by) == 0 and len(self.facets) > 1:
            raise util.CytoflowViewError("You can only facet this view if you "
                                         "specify some variables in `by`")
        
        for facet in self.facets:
            if facet not in experiment.conditions:        
                raise util.CytoflowViewError("Facet {} not in the experiment"
                                            .format(facet))
            
            if facet not in self.by:
                raise util.CytoflowViewError("Facet {} must be one of {}"
                                             .format(facet, self.by))
                
        if len(self.facets) != len(set(self.facets)):
            raise util.CytoflowViewError("You can't reuse facets!")
            
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {} not found"
                                      " in the experiment"
                                      .format(b))
                
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except util.CytoflowError as e:
                raise util.CytoflowViewError(str(e)) from e
            except Exception as e:
                raise util.CytoflowViewError("Subset string '{0}' isn't valid"
                                        .format(self.subset)) from e
                 
            if len(experiment) == 0:
                raise util.CytoflowViewError("Subset string '{0}' returned no events"
                                        .format(self.subset))
                
        by = list(set(self.by) - set(self.facets)) 
        
        class plot_enum(object):
            
            def __init__(self, by, experiment):
                self._iter = None
                self._returned = False
                
                if by:
                    self._iter = experiment.data.groupby(by).__iter__()
                
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
            
        return plot_enum(by, experiment)
    
    def plot(self, experiment, **kwargs): 

        if len(self.by) == 0 and len(self.facets) > 1:
            raise util.CytoflowViewError("You can only facet this view if you "
                                         "specify some variables in `by`")

        for facet in self.facets:
            if facet not in experiment.conditions:        
                raise util.CytoflowViewError("Facet {} not in the experiment"
                                            .format(facet))
             
            if facet not in self.by:
                raise util.CytoflowViewError("Facet {} must be one of {}"
                                             .format(facet, self.by))
                
        if len(self.facets) != len(set(self.facets)):
            raise util.CytoflowViewError("You can't reuse facets!")
            
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {} not found"
                                      " in the experiment"
                                      .format(b))
        
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
        
        by = list(set(self.by) - set(self.facets)) 
        
        plot_name = kwargs.get('plot_name', None)

        if by and plot_name is None:
            raise util.CytoflowViewError("You must use facets {} in either the "
                                         "plot facets or the plot name. "
                                         "Possible plot names: {}"
                                         .format(by, [x for x in self.enum_plots(experiment)]))
                                        
        if plot_name is not None:
            if plot_name is not None and not by:
                raise util.CytoflowViewError("Plot {} not from plot_enum"
                                             .format(plot_name))
                               
            groupby = experiment.data.groupby(by)

            if plot_name not in set(groupby.groups.keys()):
                raise util.CytoflowViewError("Plot {} not from plot_enum"
                                             .format(plot_name))
                
            experiment = experiment.clone()
            experiment.data = groupby.get_group(plot_name)
            experiment.data.reset_index(drop = True, inplace = True)
            
        super().plot(experiment, **kwargs)
        
@provides(IView)
class By1DView(ByView, Op1DView):
    pass

@provides(IView)
class By2DView(ByView, Op2DView):
    pass

@provides(IView)
class NullView(BaseDataView):
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):
        return {}


@provides(IView)
class AnnotatingView(BaseDataView):
                 
    def plot(self, experiment, **kwargs):
        annotation_facet = kwargs.pop('annotation_facet', None)
        annotation_trait = kwargs.pop('annotation_trait', None)
                
        if annotation_facet is not None and annotation_facet in experiment.data:
            if annotation_trait:
                self.trait_set(**{annotation_trait : annotation_facet})
            else:
                warn("Setting 'huefacet' to '{}'".format(annotation_facet),
                     util.CytoflowViewWarning)
                annotation_trait = 'huefacet'
                self.trait_set(**{'huefacet' : annotation_facet})                
                      
        super().plot(experiment,
                     annotation_facet = annotation_facet,
                     **kwargs)
        
    def _grid_plot(self, experiment, grid, xlim, ylim, xscale, yscale, **kwargs):
        
        # pop the annotation stuff off of kwargs so the underlying data plotter 
        # doesn't get confused
        
        annotation_facet = kwargs.pop('annotation_facet', None)
        annotations = kwargs.pop('annotations', None)
        plot_name = kwargs.pop('plot_name', None)
        color = kwargs.get('color', None)

        # plot the underlying data plots
        plot_ret = super()._grid_plot(experiment, grid, xlim, ylim, xscale, yscale, **kwargs)
                        
        # plot the annotations on top
        for (i, j, k), _ in grid.facet_data():
            ax = grid.facet_axis(i, j)
             
            row_name = grid.row_names[i] if grid.row_names and grid._row_var is not annotation_facet else None
            col_name = grid.col_names[j] if grid.col_names and grid._col_var is not annotation_facet else None
            hue_name = grid.hue_names[k] if grid.hue_names and grid._hue_var is not annotation_facet else None
             
            facets = [x for x in [row_name, col_name, hue_name] if x is not None]
            
            if plot_name is not None:
                try:
                    plot_name = list(plot_name)
                except TypeError:
                    plot_name = [plot_name]
                    
                annotation_name = plot_name + facets
            else:      
                annotation_name = facets
                
            annotation = None
            for group, a in annotations.items():
                try:
                    g_set = set(group)
                except TypeError:
                    g_set = set([group])
                if g_set == set(annotation_name):
                    annotation = a
                    
            if (annotation is None 
                and len(annotations.keys()) == 1 
                and list(annotations.keys())[0] is True):
                annotation = annotations[True]
                            
            if annotation is None:
                continue
                 
            if annotation_facet is not None:                                                  
                if annotation_facet == grid._row_var:
                    annotation_value = grid.row_names[i]
                elif annotation_facet == grid._col_var:
                    annotation_value = grid.col_names[j]
                elif annotation_facet == grid._hue_var:
                    annotation_value = grid.hue_names[k]
                else:
                    annotation_value = None
            else:
                annotation_value = None

            annotation_color = grid._facet_color(k, color)
                
            self._annotation_plot(ax, 
                                  xlim, 
                                  ylim, 
                                  xscale, 
                                  yscale, 
                                  annotation, 
                                  annotation_facet, 
                                  annotation_value, 
                                  annotation_color)

        return plot_ret
 
    def _strip_trait(self, val):
        if val:
            trait_name = self._find_trait_name(val)
            if trait_name is not None:
                view = self.clone_traits('all')
                view.trait_set(**{trait_name : ""})
                return view, trait_name
        return self, None
                             
    def _find_trait_name(self, val):
        traits = self.trait_get()
        for n, v in traits.items():
            if v == val:
                return n

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
cytoflow.operations.polygon
---------------------------

Apply a polygon gate to two channels in an `Experiment`.  
`polygon` has two classes:

`PolygonOp` -- Applies the gate, given a set of vertices.

`ScatterplotPolygonSelectionView` -- an `IView` that allows you to view the 
polygon and/or interactively set the vertices on a scatterplot.

`DensityPolygonSelectionView` -- an `IView` that allows you to view the 
polygon and/or interactively set the vertices on a scatterplot.
"""

from traits.api import (HasStrictTraits, Str, List, Float, provides,
                        Instance, Bool, observe, Any, Dict, 
                        Constant)

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.widgets import PolygonSelector
import numpy as np

import cytoflow.utility as util
from cytoflow.views import ISelectionView, ScatterplotView, DensityView

from .i_operation import IOperation
from .base_op_views import Op2DView

@provides(IOperation)
class PolygonOp(HasStrictTraits):
    """
    Apply a polygon gate to a cytometry experiment.
    
    Attributes
    ----------
    name : Str
        The operation name.  Used to name the new metadata field in the
        experiment that's created by `apply`
        
    xchannel, ychannel : Str
        The names of the x and y channels to apply the gate.
        
    xscale, yscale : {'linear', 'log', 'logicle'} (default = 'linear')
        The scales applied to the data before drawing the polygon.
        
    vertices : List((Float, Float))
        The polygon verticies.  An ordered list of 2-tuples, representing
        the x and y coordinates of the vertices.
        
    Notes
    -----
    You can set the verticies by hand, I suppose, but it's much easier to use
    the interactive view you get from `default_view` to do so.  
    Set `ScatterplotPolygonSelectionView.interactive` to `True`, then 
    single-click to set vertices. Click the first vertex a second time to 
    close the polygon.  You'll need to do this in a Jupyter notebook with
    ``%matplotlib notebook`` -- see the ``Interactive Plots`` demo for an example.

    
    Examples
    --------
    
    .. plot::
        :context: close-figs
        
        Make a little data set.
    
        >>> import cytoflow as flow
        >>> import_op = flow.ImportOp()
        >>> import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
        ...                              conditions = {'Dox' : 10.0}),
        ...                    flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
        ...                              conditions = {'Dox' : 1.0})]
        >>> import_op.conditions = {'Dox' : 'float'}
        >>> ex = import_op.apply()
    
    Create and parameterize the operation.
    
    .. plot::
        :context: close-figs
        
        >>> p = flow.PolygonOp(name = "Polygon",
        ...                    xchannel = "V2-A",
        ...                    ychannel = "Y2-A")
        >>> p.vertices = [(23.411982294776319, 5158.7027015021222), 
        ...               (102.22182270573683, 23124.058843387455), 
        ...               (510.94519955277201, 23124.058843387455), 
        ...               (1089.5215641232173, 3800.3424832180476), 
        ...               (340.56382570202402, 801.98947404942271), 
        ...               (65.42597937575897, 1119.3133482602157)]

        
    Show the default view.  

    .. plot::
        :context: close-figs
            
        >>> df = p.default_view(huefacet = "Dox",
        ...                     xscale = 'log',
        ...                     yscale = 'log',
        ...                     density = True)
        
        >>> df.plot(ex)
        
    
    .. note::
       If you want to use the interactive default view in a Jupyter notebook,
       make sure you say ``%matplotlib notebook`` in the first cell 
       (instead of ``%matplotlib inline`` or similar).  Then call 
       `default_view` with ``interactive = True``::
       
           df = p.default_view(huefacet = "Dox",
                               xscale = 'log',
                               yscale = 'log',
                               interactive = True)
           df.plot(ex)
        
    Apply the gate, and show the result
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = p.apply(ex)
        >>> ex2.data.groupby('Polygon').size()
        Polygon
        False    15875
        True      4125
        dtype: int64
            
    You can also get (or draw) the polygon on a density plot instead of a 
    scatterplot:
    
    .. plot::
        :context: close-figs
            
        >>> df = p.default_view(huefacet = "Dox",
        ...                     xscale = 'log',
        ...                     yscale = 'log')
        
        >>> df.plot(ex)
    """
    
    # traits
    id = Constant('cytoflow.operations.polygon')
    friendly_id = Constant("Polygon")
    
    name = Str
    xchannel = Str
    ychannel = Str
    vertices = List((Float, Float))
    
    xscale = util.ScaleEnum()
    yscale = util.ScaleEnum()
    
    _selection_view = Instance('_PolygonSelection', transient = True)
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old `Experiment` to which this op is applied
            
        Returns
        -------
        Experiment
            a new 'Experiment`, the same as ``experiment`` but with 
            a new column of type `bool` with the same as the operation name.  
            The bool is ``True`` if the event's measurement is within the 
            polygon, and ``False`` otherwise.
            
        Raises
        ------
        CytoflowOpError
            if for some reason the operation can't be applied to this
            experiment. The reason is in the ``args`` attribute.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
            
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the Polygon gate's name "
                                       "before applying it!")

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       "{} is in the experiment already!"
                                       .format(self.name))
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name)) 
        
        if not self.xchannel:
            raise util.CytoflowOpError('xchannel',
                                       "Must specify an x channel")

        if not self.ychannel:
            raise util.CytoflowOpError('ychannel',
                                       "Must specify a y channel")
        
        if not self.xchannel in experiment.channels:
            raise util.CytoflowOpError('xchannel',
                                       "xchannel {0} is not in the experiment"
                                       .format(self.xchannel))
                                  
        if not self.ychannel in experiment.channels:
            raise util.CytoflowOpError('ychannel',
                                       "ychannel {0} is not in the experiment"
                                       .format(self.ychannel))
              
        if len(self.vertices) < 3:
            raise util.CytoflowOpError('vertices',
                                       "Must have at least 3 vertices")
       
        if any([len(x) != 2 for x in self.vertices]):
            return util.CytoflowOpError('vertices',
                                        "All vertices must be lists or tuples "
                                        "of length = 2") 
            
        # there's a bit of a subtlety here: if the vertices were 
        # selected with an interactive plot, and that plot had scaled
        # axes, we need to apply that scale function to both the
        # vertices and the data before looking for path membership.
        # if you set xscale and yscale via arguments to default_view, 
        # the operations' get set as well (because PolygonSelection.xscale
        # and PolygonSelection.yscale are delegates to PolygonSelection.op)
        xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)
        yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
        
        vertices = [(xscale(x), yscale(y)) for (x, y) in self.vertices]
        vertices.append(vertices[0])
        data = experiment.data[[self.xchannel, self.ychannel]].copy()
        data[self.xchannel] = xscale(data[self.xchannel])
        data[self.ychannel] = yscale(data[self.ychannel])
        
        # use an extremely fast parallel algorithm to test polygon membership.
        # this function is better defined for edge cases than matplotlib's
        # path.contains_points.  and it's faster.
        # see https://stackoverflow.com/questions/36399381/whats-the-fastest-way-of-checking-if-a-point-is-inside-a-polygon-in-python
        # for a deep dive
        xy_data = data[[self.xchannel, self.ychannel]].values
        in_polygon = util.polygon_contains(xy_data, np.array(vertices))
        
        new_experiment = experiment.clone(deep = False)        
        new_experiment.add_condition(self.name, "bool", in_polygon)
        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
            
        return new_experiment
    
    def default_view(self, **kwargs):
        """
        Returns an `IView` that allows a user to view the polygon or interactively draw it.
        
        Parameters
        ----------
        
        density : bool, default = False
            If `True`, return a density plot instead of a scatterplot.
        """ 
        
        density = kwargs.pop('density', False)
        if density:
            self._selection_view = DensityPolygonSelectionView(op = self)
        else:
            self._selection_view = ScatterplotPolygonSelectionView(op = self)
            
        self._selection_view.trait_set(**kwargs)
        return self._selection_view
    
    
class _PolygonSelection(Op2DView):    
    xfacet = Constant(None)
    yfacet = Constant(None)

    interactive = Bool(False, transient = True)

    # internal state.
    _ax = Any(transient = True)
    _widget = Instance(PolygonSelector, transient = True)
    _patch = Instance(mpl.patches.PathPatch, transient = True)
    _patch_props = Dict()
        
    def plot(self, experiment, **kwargs):
        
        if experiment is None:
            raise util.CytoflowViewError('experiment',
                                         "No experiment specified")
            
        self._patch_props = kwargs.pop('patch_props',
                                        {'edgecolor' : 'black',
                                         'linewidth' : 2,
                                         'fill' : False})
        
        super(_PolygonSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_poly(None)
        self._interactive(None)
    

    @observe('op.vertices', post_init = True)        
    def _draw_poly(self, _):
        if not self._ax:
            return
         
        if self._patch and self._patch in self._ax.patches:
            self._patch.remove()
            
        if not self.op.vertices or len(self.op.vertices) < 3:
            return
             
        patch_vert = np.concatenate((np.array(self.op.vertices), 
                                    np.array((0,0), ndmin = 2)))
        
        self._patch = \
            mpl.patches.PathPatch(mpl.path.Path(patch_vert, closed = True), **self._patch_props)
            
        self._ax.add_patch(self._patch)
        plt.draw()
    
    @observe('interactive', post_init = True)
    def _interactive(self, _):
        if self._ax and self.interactive:
            self._widget = PolygonSelector(self._ax,
                                           self._onselect,
                                           useblit = True,
                                           grab_range = 20)
        elif self._widget:
            self._widget.set_active(False) 
            self._widget = None    
     
    def _onselect(self, vertices):
        self.op.vertices = vertices
        self.interactive = False
  

@provides(ISelectionView)
class ScatterplotPolygonSelectionView(_PolygonSelection, ScatterplotView):
    """
    Plots, and lets the user interact with, a 2D polygon selection on a scatterplot.
    
    Attributes
    ----------
    interactive : bool
        is this view interactive?  Ie, can the user set the polygon verticies
        with mouse clicks?
        
    Examples
    --------

    In a Jupyter notebook with ``%matplotlib notebook``
    
    >>> s = flow.PolygonOp(xchannel = "V2-A",
    ...                    ychannel = "Y2-A")
    >>> poly = s.default_view()
    >>> poly.plot(ex2)
    >>> poly.interactive = True
    """
    
    id = Constant('cytoflow.views.polygon')
    friendly_id = Constant("Polygon Selection")
    
    def plot(self, experiment, **kwargs):
        """
        Plot the default view, and then draw the selection on top of it.
        
        Parameters
        ----------
        
        patch_props : Dict
           The properties of the `matplotlib.patches.Patch` that are drawn
           on top of the scatterplot or density view.  They're passed
           directly to the `matplotlib.patches.Patch` constructor.
           Default: ``{edgecolor : 'black', linewidth : 2, fill : False}``
        
        """
        super().plot(experiment, **kwargs)

util.expand_class_attributes(ScatterplotPolygonSelectionView)
util.expand_method_parameters(ScatterplotPolygonSelectionView, ScatterplotPolygonSelectionView.plot) 

@provides(ISelectionView)
class DensityPolygonSelectionView(_PolygonSelection, DensityView):
    """
    Plots, and lets the user interact with, a 2D polygon selection on a density plot.
    
    Attributes
    ----------
    interactive : bool
        is this view interactive?  Ie, can the user set the polygon verticies
        with mouse clicks?
        
    Examples
    --------

    In a Jupyter notebook with ``%matplotlib notebook``
    
    >>> s = flow.PolygonOp(xchannel = "V2-A",
    ...                    ychannel = "Y2-A")
    >>> poly = s.default_view(density = True)
    >>> poly.plot(ex2)
    >>> poly.interactive = True
    """
    
    id = Constant('cytoflow.views.polygon_density')
    friendly_id = Constant("Polygon Selection")
    
    def plot(self, experiment, **kwargs):
        """
        Plot the default view, and then draw the selection on top of it.
        
        Parameters
        ----------
        
        patch_props : Dict
           The properties of the `matplotlib.patches.Patch` that are drawn
           on top of the scatterplot or density view.  They're passed
           directly to the `matplotlib.patches.Patch` constructor.
           Default: {edgecolor : 'black', linewidth : 2, fill : False}
        
        """
        super().plot(experiment, **kwargs)

util.expand_class_attributes(DensityPolygonSelectionView)
util.expand_method_parameters(ScatterplotPolygonSelectionView, ScatterplotPolygonSelectionView.plot) 
        
if __name__ == '__main__':
    import cytoflow as flow
    tube1 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs',
                      conditions = {"Dox" : 10.0})
    
    tube2 = flow.Tube(file = '../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs',
                      conditions = {"Dox" : 1.0})                      

    ex = flow.ImportOp(conditions = {"Dox" : "float"}, tubes = [tube1, tube2])
    
    p = PolygonOp(xchannel = "V2-A",
                  ychannel = "Y2-A")
    v = p.default_view(xscale = "logicle", yscale = "logicle")
    
    plt.ioff()
    v.plot(ex)
    v.interactive = True
    plt.show()

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
cytoflow.operations.polygon
---------------------------
'''

from traits.api import (HasStrictTraits, Str, CStr, List, Float, provides,
                        Instance, Bool, on_trait_change, Any,
                        Constant)

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

import cytoflow.utility as util
from cytoflow.views import ISelectionView, ScatterplotView

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
        experiment that's created by :meth:`apply`
        
    xchannel, ychannel : Str
        The names of the x and y channels to apply the gate.
        
    xscale, yscale : {'linear', 'log', 'logicle'} (default = 'linear')
        The scales applied to the data before drawing the polygon.
        
    vertices : List((Float, Float))
        The polygon verticies.  An ordered list of 2-tuples, representing
        the x and y coordinates of the vertices.
        
    Notes
    -----
    This module uses :meth:`matplotlib.path.Path` to represent the polygon, because
    membership testing is very fast.
    
    You can set the verticies by hand, I suppose, but it's much easier to use
    the interactive view you get from :meth:`default_view` to do so.
    
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
            
        >>> p.default_view(huefacet = "Dox",
        ...                xscale = 'log',
        ...                yscale = 'log').plot(ex)
        
    Apply the gate, and show the result
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = p.apply(ex)
        >>> ex2.data.groupby('Polygon').size()
        Polygon
        False    15875
        True      4125
        dtype: int64
            
    """
    
    # traits
    id = Constant('edu.mit.synbio.cytoflow.operations.polygon')
    friendly_id = Constant("Polygon")
    
    name = CStr()
    xchannel = Str()
    ychannel = Str()
    vertices = List((Float, Float))
    
    xscale = util.ScaleEnum()
    yscale = util.ScaleEnum()
        
    def apply(self, experiment):
        """Applies the threshold to an experiment.
        
        Parameters
        ----------
        experiment : Experiment
            the old :class:`Experiment` to which this op is applied
            
        Returns
        -------
        Experiment
            a new :class:'Experiment`, the same as ``old_experiment`` but with 
            a new column of type `bool` with the same as the operation name.  
            The bool is ``True`` if the event's measurement is within the 
            polygon, and ``False`` otherwise.
            
        Raises
        ------
        util.CytoflowOpError
            if for some reason the operation can't be applied to this
            experiment. The reason is in :attr:`.CytoflowOpError.args`
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       "{} is in the experiment already!"
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
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the Polygon gate's name "
                                       "before applying it!")
        
        # make sure old_experiment doesn't already have a column named self.name
        if(self.name in experiment.data.columns):
            raise util.CytoflowOpError('name',
                                       "Experiment already contains a column {0}"
                                       .format(self.name))
            
        # there's a bit of a subtlety here: if the vertices were 
        # selected with an interactive plot, and that plot had scaled
        # axes, we need to apply that scale function to both the
        # vertices and the data before looking for path membership
        xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)
        yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
        
        vertices = [(xscale(x), yscale(y)) for (x, y) in self.vertices]
        data = experiment.data[[self.xchannel, self.ychannel]].copy()
        data[self.xchannel] = xscale(data[self.xchannel])
        data[self.ychannel] = yscale(data[self.ychannel])
            
        # use a matplotlib Path because testing for membership is a fast C fn.
        path = mpl.path.Path(np.array(vertices))
        xy_data = data.as_matrix(columns = [self.xchannel, self.ychannel])
        
        new_experiment = experiment.clone()        
        new_experiment.add_condition(self.name, 
                                     "bool", 
                                     path.contains_points(xy_data))
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
            
        return new_experiment
    
    def default_view(self, **kwargs):
        p = PolygonSelection(op = self)
        p.trait_set(**kwargs)
        return p 
    
@provides(ISelectionView)
class PolygonSelection(Op2DView, ScatterplotView):
    """
    Plots, and lets the user interact with, a 2D polygon selection.
    
    Attributes
    ----------
    interactive : bool
        is this view interactive?  Ie, can the user set the polygon verticies
        with mouse clicks?
        
    Examples
    --------

    In a Jupyter notebook with `%matplotlib notebook`
    
    >>> s = flow.PolygonOp(xchannel = "V2-A",
    ...                    ychannel = "Y2-A")
    >>> poly = s.default_view()
    >>> poly.plot(ex2)
    >>> poly.interactive = True
    """
    
    id = Constant('edu.mit.synbio.cytoflow.views.polygon')
    friendly_id = Constant("Polygon Selection")
    
    xfacet = Constant(None)
    yfacet = Constant(None)

    interactive = Bool(False, transient = True)

    # internal state.
    _ax = Any(transient = True)
    _widget = Instance(util.PolygonSelector, transient = True)
    _patch = Instance(mpl.patches.PathPatch, transient = True)
        
    def plot(self, experiment, **kwargs):
        """
        Plot the scatter plot, and then plot the selection on top of it.
        
        Parameters
        ----------
        
        """
        
        super(PolygonSelection, self).plot(experiment, **kwargs)
        self._ax = plt.gca()
        self._draw_poly()
        self._interactive()
    
    @on_trait_change('op.vertices', post_init = True)
    def _draw_poly(self):
        if not self._ax:
            return
         
        if self._patch and self._patch in self._ax.patches:
            self._patch.remove()
            
        if not self.op.vertices or len(self.op.vertices) < 3:
            return
             
        patch_vert = np.concatenate((np.array(self.op.vertices), 
                                    np.array((0,0), ndmin = 2)))
                                    
        self._patch = \
            mpl.patches.PathPatch(mpl.path.Path(patch_vert, closed = True),
                                  edgecolor="black",
                                  linewidth = 2,
                                  fill = False)
            
        self._ax.add_patch(self._patch)
        plt.draw()
    
    @on_trait_change('interactive', post_init = True)
    def _interactive(self):
        if self._ax and self.interactive:
            self._widget = util.PolygonSelector(self._ax,
                                                self._onselect,
                                                useblit = True)
        elif self._widget:
            self._widget = None       
    
    def _onselect(self, vertices):
        self.op.vertices = vertices
    
util.expand_class_attributes(PolygonSelection)
util.expand_method_parameters(PolygonSelection, PolygonSelection.plot)        
        
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

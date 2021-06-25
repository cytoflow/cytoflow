#!/usr/bin/env python3.4
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

'''
cytoflow.operations.density
---------------------------
'''

from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, 
                        Constant, List, provides, Array)

import numpy as np
import scipy.stats
import scipy.ndimage.filters
import pandas as pd

from cytoflow.views import IView, DensityView
import cytoflow.utility as util

from .i_operation import IOperation
from .base_op_views import By2DView, AnnotatingView

@provides(IOperation)
class DensityGateOp(HasStrictTraits):
    """
    This module computes a gate based on a 2D density plot.  The user chooses
    what proportion of events to keep, and the module creates a gate that selects
    that proportion of events in the highest-density bins of the 2D density
    histogram.
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    xchannel : Str
        The X channel to apply the binning to.
        
    ychannel : Str
        The Y channel to apply the binning to.

    xscale : {"linear", "logicle", "log"} (default = "linear")
        Re-scale the data on the X acis before fitting the data?  

    yscale : {"linear", "logicle", "log"} (default = "linear")
        Re-scale the data on the Y axis before fitting the data?  
        
    keep : Float (default = 0.9)
        What proportion of events to keep?  Must be ``>0`` and ``<1`` 
        
    bins : Int (default = 100)
        How many bins should there be on each axis?  Must be positive.
        
    min_quantile : Float (default = 0.001)
        Clip values below this quantile
        
    max_quantile : Float (default = 1.0)
        Clip values above this quantile

    sigma : Float (default = 1.0)
        What standard deviation to use for the gaussian blur?
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the gate.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting ``by = ["Time", "Dox"]`` will fit a 
        separate gate to each subset of the data with a unique combination of
        ``Time`` and ``Dox``.
        
    Notes
    -----
    This gating method was developed by John Sexton, in Jeff Tabor's lab at
    Rice University.  
    
    From http://taborlab.github.io/FlowCal/fundamentals/density_gate.html,
    the method is as follows:
    
    1. Determines the number of events to keep, based on the user specified 
       gating fraction and the total number of events of the input sample.
       
    2. Divides the 2D channel space into a rectangular grid, and counts the 
       number of events falling within each bin of the grid. The number of 
       counts per bin across all bins comprises a 2D histogram, which is a 
       coarse approximation of the underlying probability density function.
       
    3. Smoothes the histogram generated in Step 2 by applying a Gaussian Blur. 
       Theoretically, the proper amount of smoothing results in a better 
       estimate of the probability density function. Practically, smoothing 
       eliminates isolated bins with high counts, most likely corresponding to 
       noise, and smoothes the contour of the gated region.
       
    4. Selects the bins with the greatest number of events in the smoothed 
       histogram, starting with the highest and proceeding downward until the 
       desired number of events to keep, calculated in step 1, is achieved.
    
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
        
        >>> dens_op = flow.DensityGateOp(name = 'Density',
        ...                              xchannel = 'FSC-A',
        ...                              xscale = 'log',
        ...                              ychannel = 'SSC-A',
        ...                              yscale = 'log',
        ...                              keep = 0.5)
        
    Find the bins to keep
    
    .. plot::
        :context: close-figs
        
        >>> dens_op.estimate(ex)
        
    Plot a diagnostic view
    
    .. plot::
        :context: close-figs
        
        >>> dens_op.default_view().plot(ex)
        
    Apply the gate
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = dens_op.apply(ex)
        
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.density')
    friendly_id = Constant("Density Gate")
    
    name = Str
    xchannel = Str
    ychannel = Str
    xscale = util.ScaleEnum
    yscale = util.ScaleEnum
    keep = util.PositiveFloat(0.9, allow_zero = False)
    bins = util.PositiveInt(100, allow_zero = False)
    min_quantile = util.PositiveFloat(0.001, allow_zero = True)
    max_quantile = util.PositiveFloat(1.0, allow_zero = False)
    sigma = util.PositiveFloat(1.0, allow_zero = False)
    by = List(Str)
        
    _xscale = Instance(util.IScale, transient = True)
    _yscale = Instance(util.IScale, transient = True)
    
    _xbins = Array(transient = True)
    _ybins = Array(transient = True)

    _keep_xbins = Dict(Any, Array, transient = True)
    _keep_ybins = Dict(Any, Array, transient = True)
    _histogram = Dict(Any, Array, transient = True)
    
    def estimate(self, experiment, subset = None):
        """
        Split the data set into bins and determine which ones to keep.
        
        Parameters
        ----------
        experiment : Experiment
            The :class:`.Experiment` to use to estimate the gate parameters.
            
        subset : Str (default = None)
            If set, determine the gate parameters on only a subset of the
            ``experiment`` parameter.
        """
        
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")

        if self.xchannel not in experiment.data:
            raise util.CytoflowOpError('xchannel',
                                       "Column {0} not found in the experiment"
                                       .format(self.xchannel))
            
        if self.ychannel not in experiment.data:
            raise util.CytoflowOpError('ychannel',
                                       "Column {0} not found in the experiment"
                                       .format(self.ychannel))

        if self.min_quantile > 1.0:
            raise util.CytoflowOpError('min_quantile',
                                       "min_quantile must be <= 1.0")
            
        if self.max_quantile > 1.0:
            raise util.CytoflowOpError('max_quantile',
                                       "max_quantile must be <= 1.0")
               
        if not (self.max_quantile > self.min_quantile):
            raise util.CytoflowOpError('max_quantile',
                                       "max_quantile must be > min_quantile")
        
        if self.keep > 1.0:
            raise util.CytoflowOpError('keep',
                                       "keep must be <= 1.0")

        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
                
        if subset:
            try:
                experiment = experiment.query(subset)
            except:
                raise util.CytoflowOpError('subset',
                                            "Subset string '{0}' isn't valid"
                                            .format(subset))
                
            if len(experiment) == 0:
                raise util.CytoflowOpError('subset',
                                           "Subset string '{0}' returned no events"
                                           .format(subset))
                
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda _: True)
            
        # get the scale. estimate the scale params for the ENTIRE data set,
        # not subsets we get from groupby().  And we need to save it so that
        # the data is transformed the same way when we apply()
        self._xscale = xscale = util.scale_factory(self.xscale, experiment, channel = self.xchannel)
        self._yscale = yscale = util.scale_factory(self.yscale, experiment, channel = self.ychannel)
        

        xlim = (xscale.clip(experiment[self.xchannel].quantile(self.min_quantile)),
                xscale.clip(experiment[self.xchannel].quantile(self.max_quantile)))
                  
        ylim = (yscale.clip(experiment[self.ychannel].quantile(self.min_quantile)),
                yscale.clip(experiment[self.ychannel].quantile(self.max_quantile)))
        
        self._xbins = xbins = xscale.inverse(np.linspace(xscale(xlim[0]), 
                                                         xscale(xlim[1]), 
                                                         self.bins))
        self._ybins = ybins = yscale.inverse(np.linspace(yscale(ylim[0]), 
                                                         yscale(ylim[1]), 
                                                         self.bins))
                    
        histogram = {}
        for group, group_data in groupby:
            if len(group_data) == 0:
                raise util.CytoflowOpError('by',
                                           "Group {} had no data"
                                           .format(group))

            h, _, _ = np.histogram2d(group_data[self.xchannel], 
                                     group_data[self.ychannel], 
                                     bins=[xbins, ybins])
            
            h = scipy.ndimage.filters.gaussian_filter(h, sigma = self.sigma)
            
            i = scipy.stats.rankdata(h, method = "ordinal") - 1
            i = np.unravel_index(np.argsort(-i), h.shape)
            
            goal_count = self.keep * len(group_data)
            curr_count = 0
            num_bins = 0

            while(curr_count < goal_count and num_bins < i[0].size):
                curr_count += h[i[0][num_bins], i[1][num_bins]]
                num_bins += 1
                
            self._keep_xbins[group] = i[0][0:num_bins]
            self._keep_ybins[group] = i[1][0:num_bins]
            histogram[group] = h
            
        self._histogram = histogram

            
    def apply(self, experiment):
        """
        Creates a new condition based on membership in the gate that was
        parameterized with :meth:`estimate`.
        
        Parameters
        ----------
        experiment : Experiment
            the :class:`.Experiment` to apply the gate to.
            
        Returns
        -------
        Experiment
            a new :class:`.Experiment` with the new gate applied.
        """
            
        if experiment is None:
            raise util.CytoflowOpError('experiment',
                                       "No experiment specified")
        
        if not self.xchannel:
            raise util.CytoflowOpError('xchannel',
                                       "Must set X channel")

        if not self.ychannel:
            raise util.CytoflowOpError('ychannel',
                                       "Must set Y channel")
        
        # make sure name got set!
        if not self.name:
            raise util.CytoflowOpError('name',
                                       "You have to set the gate's name "
                                       "before applying it!")
            
        if self.name != util.sanitize_identifier(self.name):
            raise util.CytoflowOpError('name',
                                       "Name can only contain letters, numbers and underscores."
                                       .format(self.name))  

        if self.name in experiment.data.columns:
            raise util.CytoflowOpError('name',
                                       "Experiment already has a column named {0}"
                                       .format(self.name))
        
        if not (self._xbins.size and self._ybins.size and self._keep_xbins):
            raise util.CytoflowOpError(None,
                                       "No gate estimate found.  Did you forget to "
                                       "call estimate()?")

        if not self._xscale:
            raise util.CytoflowOpError(None,
                                       "Couldn't find _xscale.  What happened??")
        
        if not self._yscale:
            raise util.CytoflowOpError(None,
                                       "Couldn't find _yscale.  What happened??")

        if self.xchannel not in experiment.data:
            raise util.CytoflowOpError('xchannel',
                                       "Column {0} not found in the experiment"
                                       .format(self.xchannel))

        if self.ychannel not in experiment.data:
            raise util.CytoflowOpError('ychannel',
                                       "Column {0} not found in the experiment"
                                       .format(self.ychannel))
       
        for b in self.by:
            if b not in experiment.conditions:
                raise util.CytoflowOpError('by',
                                           "Aggregation metadata {} not found, "
                                           "must be one of {}"
                                           .format(b, experiment.conditions))
        
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that
            # contains all the events
            groupby = experiment.data.groupby(lambda _: True)
            
        event_assignments = pd.Series([False] * len(experiment), dtype = "bool")
        
        for group, group_data in groupby:
            if group not in self._keep_xbins:
                # there weren't any events in this group, so we didn't get
                # an estimate
                continue
            
            group_idx = groupby.groups[group]
            
            cX = pd.cut(group_data[self.xchannel], self._xbins, include_lowest = True, labels = False).reset_index(drop = True)
            cY = pd.cut(group_data[self.ychannel], self._ybins, include_lowest = True, labels = False).reset_index(drop = True)

            group_keep = pd.Series([False] * len(group_data))
            
            keep_x = self._keep_xbins[group]
            keep_y = self._keep_ybins[group]
            
            for (xbin, ybin) in zip(keep_x, keep_y):
                group_keep = group_keep | ((cX == xbin) & (cY == ybin))
                            
            event_assignments.iloc[group_idx] = group_keep
                    
        new_experiment = experiment.clone()
        
        new_experiment.add_condition(self.name, "bool", event_assignments)

        new_experiment.history.append(self.clone_traits(transient = lambda _: True))
        return new_experiment
     
    def default_view(self, **kwargs):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
         
        Returns
        -------
        IView
            a diagnostic view, call :meth:`~DensityGateView.plot` to see the 
            diagnostic plot.
        """
        v = DensityGateView(op = self)
        v.trait_set(**kwargs)
        return v
          
@provides(IView)
class DensityGateView(By2DView, AnnotatingView, DensityView):
    """
    A diagnostic view for :class:`DensityGateOp`.  Draws a density plot,
    then outlines the selected bins in white.
    
    Attributes
    ----------
    
    """
     
    id = Constant('edu.mit.synbio.cytoflow.view.densitygateview')
    friendly_id = Constant("Density Gate Diagnostic Plot")

    huefacet = Constant(None)
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        
        Parameters
        ----------
        
        """
        
        annotations = {}
        for i in self.op._keep_xbins:
            annotations[i] = (self.op._keep_xbins[i],
                              self.op._keep_ybins[i],
                              self.op._histogram[i])
        
        super().plot(experiment,
                     annotations = annotations,
                     xscale = self.op._xscale,
                     yscale = self.op._yscale,
                     **kwargs)
     
    def _annotation_plot(self, 
                         axes, 
                         annotation, 
                         annotation_facet, 
                         annotation_value, 
                         annotation_color, 
                         **kwargs):
        # plot a countour around the bins that got kept
  
        keep_x = annotation[0]
        keep_y = annotation[1]
        h = annotation[2]
        xbins = self.op._xbins[0:-1]
        ybins = self.op._ybins[0:-1]
        last_level = h[keep_x[-1], keep_y[-1]]

        axes.contour(xbins, ybins, h.T, [last_level], colors = 'w')
        
util.expand_class_attributes(DensityGateView)
util.expand_method_parameters(DensityGateView, DensityGateView.plot)

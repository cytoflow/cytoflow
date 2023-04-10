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
cytoflow.operations.UMAP
-----------------------

Apply principal component analysis (UMAP) to flow data -- decomposes the
multivariate data set into orthogonal components that explain the maximum
amount of variance.  `UMAP` has one class:

`UMAPOp` -- the `IOperation` that applies UMAP to an `Experiment`.
"""


from traits.api import (HasStrictTraits, Str, Dict, Any, Instance, 
                        Constant, List, Float, provides)

import numpy as np
import pandas as pd
import umap

import cytoflow.utility as util
from .i_operation import IOperation
from .base_dimensionality_reduction_op import BaseDimensionalityReductionOp

@provides(IOperation)
class UMAPOp(BaseDimensionalityReductionOp):
    """
    Use Uniform Manifold Approximation and Projection (UMAP) to project a multivariate data
    set into a low dimensional embedding of the data such that the representing graph of the data points in the embedding
      is as structurally similar as possible to the graph in high dimension.

    Call `estimate` to compute fit the umap on the data.
      
    Calling `apply` creates new "channels" named ``{name}_1 ... {name}_n``,
    where ``name`` is the `name` attribute and ``n`` is `num_components`.

    The same dimensionality reduction may not be appropriate for different subsets of the data set.
    If this is the case, you can use the `by` attribute to specify 
    metadata by which to aggregate the data before estimating (and applying) a 
    model.  The UMAP parameters such as the number of components are the same 
    across each subset, though.

    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new columns.
        
    channels : List(Str)
        The channels to apply the decomposition to.

    scale : Dict(Str : {"linear", "logicle", "log"})
        Re-scale the data in the specified channels before fitting.  If a 
        channel is in `channels` but not in `scale`, the current 
        package-wide default (set with `set_default_scale`) is used.

    num_components : Int (default = 2)
        How many components to fit to the data?  Must be a positive integer.

    n_neighbors : Int (default = 15)
        The size of local neighborhood (in terms of number of neighboring 
        sample points) used for manifold approximation. Larger values result 
        in more global views of the manifold, while smaller values result in 
        more local data being preserved. For more information check out the
        UMAP documentation.
    
    min_dist : Float (default = 0.1)
        The effective minimum distance between embedded points. Smaller values
        will result in a more clustered/clumped embedding where nearby points
        on the manifold are drawn closer together, while larger values will 
        result on a more even dispersal of points

    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        ``Time`` and ``Dox``, setting `by` to ``["Time", "Dox"]`` will 
        fit the model separately to each subset of the data with a unique 
        combination of ``Time`` and ``Dox``.
        
    whiten : Bool (default = False)
        Scale each component to unit variance?  May be useful if you will
        be using unsupervized clustering (such as K-means).

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
        
        >>> UMAP = flow.UMAPOp(name = 'UMAP',
        ...                  channels = ['V2-A', 'V2-H', 'Y2-A', 'Y2-H'],
        ...                  scale = {'V2-A' : 'log',
        ...                           'V2-H' : 'log',
        ...                           'Y2-A' : 'log',
        ...                           'Y2-H' : 'log'},
        ...                  num_components = 2,
        ...                  by = ["Dox"])
        
    Estimate the decomposition
    
    .. plot::
        :context: close-figs
        
        >>> UMAP.estimate(ex)
        
    Apply the operation
    
    .. plot::
        :context: close-figs
        
        >>> ex2 = UMAP.apply(ex)

    Plot a scatterplot of the UMAP. Compare to a scatterplot of the underlying
    channels.
    
    .. plot::
        :context: close-figs
        
        >>> flow.ScatterplotView(xchannel = "V2-A",
        ...                      xscale = "log",
        ...                      ychannel = "Y2-A",
        ...                      yscale = "log",
        ...                      subset = "Dox == 1.0").plot(ex2)

        >>> flow.ScatterplotView(xchannel = "UMAP_1",
        ...                      ychannel = "UMAP_2",
        ...                      subset = "Dox == 1.0").plot(ex2)
       
    .. plot::
        :context: close-figs
        
        >>> flow.ScatterplotView(xchannel = "V2-A",
        ...                      xscale = "log",
        ...                      ychannel = "Y2-A",
        ...                      yscale = "log",
        ...                      subset = "Dox == 10.0").plot(ex2) 

        >>> flow.ScatterplotView(xchannel = "UMAP_1",
        ...                      ychannel = "UMAP_2",
        ...                      subset = "Dox == 10.0").plot(ex2)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.umap')
    friendly_id = Constant("Uniform Manifold Approximation and Projection (UMAP)")
    
    n_neighbors = util.PositiveInt(2, allow_zero = False)
    min_dist = util.PositiveFloat(0.1, allow_zero = True)

    def _validate_estimate(self, experiment, subset = None):
        """
        Check that the user-specified parameters are valid.
        """
        
        if self.n_neighbors > len(experiment):
            raise util.CytoflowOpError('n_neighbors',
                                       "Number of neighbors must be less than "
                                       "or equal to number of data points.")
    
    def _init_embedder(self, group, data_subset):
        return umap.UMAP(n_neighbors=self.n_neighbors, n_components= self.num_components)
    
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the decomposition
        
        Parameters
        ----------
        experiment : Experiment
            The `Experiment` to use to estimate the UMAP projection.
            
        subset : str (default = None)
            A Python expression that specifies a subset of the data in 
            ``experiment`` to use to parameterize the operation.

        """
        super().estimate(experiment, subset)
                          
         
    def apply(self, experiment):
        """
        Apply the UMAP projection to the data.
        
        Returns
        -------
        Experiment
            a new Experiment with additional `Experiment.channels` 
            named ``name_1 ... name_n``

        """
        return super().apply(experiment)

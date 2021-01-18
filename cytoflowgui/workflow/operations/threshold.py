#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
Threshold Gate
--------------

Draw a threshold gate.  To set a new threshold, click on the plot.

.. object:: Name

    The operation name.  Used to name the new metadata field that's created by 
    this module.
    
.. object:: Channel

    The name of the channel to apply the gate to.

.. object:: Threshold

    The threshold of the gate.
    
.. object:: Scale

    The scale of the axis for the interactive plot
    
.. object:: Hue facet

    Show different experimental conditions in different colors.
    
.. object:: Subset

    Show only a subset of the data.
   
.. plot::

    import cytoflow as flow
    import_op = flow.ImportOp()
    import_op.tubes = [flow.Tube(file = "Plate01/RFP_Well_A3.fcs",
                                 conditions = {'Dox' : 10.0}),
                       flow.Tube(file = "Plate01/CFP_Well_A4.fcs",
                                 conditions = {'Dox' : 1.0})]
    import_op.conditions = {'Dox' : 'float'}
    ex = import_op.apply()

    thresh_op = flow.ThresholdOp(name = 'Threshold',
                                 channel = 'Y2-A',
                                 threshold = 2000)

    thresh_op.default_view(scale = 'log').plot(ex)
    
'''

from traits.api import provides, Instance, Str, CFloat, DelegatesTo

from cytoflow.operations.threshold import ThresholdOp, ThresholdSelection

from .. import Changed
from ..views.i_workflow_view import IWorkflowView
from ..views.histogram import HistogramPlotParams
from ..serialization import camel_registry, traits_str, traits_repr, dedent

from .operation_base import IWorkflowOperation


ThresholdOp.__repr__ = traits_repr

@provides(IWorkflowView)
class ThresholdSelectionView(ThresholdSelection):
    op = Instance(IWorkflowOperation, fixed = True)
    threshold = DelegatesTo('op', status = True)
    plot_params = Instance(HistogramPlotParams, ())
    name = Str
    
    def should_plot(self, changed, payload):
        if changed == Changed.PREV_RESULT or changed == Changed.VIEW:
            return True
        else:
            return False
        
    def plot_wi(self, wi):        
        self.plot(wi.previous_wi.result, **self.plot_params.trait_get())
        
    def get_notebook_code(self, idx):
        view = ThresholdSelection()
        view.copy_traits(self, view.copyable_trait_names())
        plot_params_str = traits_str(self.plot_params)
        
        return dedent("""
        op_{idx}.default_view({traits}).plot(ex_{prev_idx}{plot_params})
        """
        .format(idx = idx, 
                traits = traits_str(view),
                prev_idx = idx - 1,
                plot_params = ", " + plot_params_str if plot_params_str else ""))
    
@provides(IWorkflowOperation)
class ThresholdWorkflowOp(ThresholdOp):
    threshold = CFloat
     
    def default_view(self, **kwargs):
        return ThresholdSelectionView(op = self, **kwargs)
    
    def get_notebook_code(self, idx):
        op = ThresholdOp()
        op.copy_traits(self, op.copyable_trait_names())

        return dedent("""
        op_{idx} = {repr}
                
        ex_{idx} = op_{idx}.apply(ex_{prev_idx})
        """
        .format(repr = repr(op),
                idx = idx,
                prev_idx = idx - 1))

    
### Serialization
@camel_registry.dumper(ThresholdWorkflowOp, 'threshold', version = 1)
def _dump(op):
    return dict(name = op.name,
                channel = op.channel,
                threshold = op.threshold)
    
@camel_registry.loader('threshold', version = 1)
def _load(data, version):
    return ThresholdWorkflowOp(**data)

@camel_registry.dumper(ThresholdSelectionView, 'threshold-view', version = 2)
def _dump_view(view):
    return dict(op = view.op,
                scale = view.scale,
                huefacet = view.huefacet,
                subset_list = view.subset_list,
                plot_params = view.plot_params,
                current_plot = view.current_plot)
    
@camel_registry.dumper(ThresholdSelectionView, 'threshold-view', version = 1)
def _dump_view_v1(view):
    return dict(op = view.op,
                scale = view.scale,
                huefacet = view.huefacet,
                subset_list = view.subset_list)
    
@camel_registry.loader('threshold-view', version = any)
def _load_view(data, version):
    return ThresholdSelectionView(**data)
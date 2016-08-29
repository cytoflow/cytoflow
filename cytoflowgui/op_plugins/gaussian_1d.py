#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
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
Created on Oct 9, 2015

@author: brian
'''

import random, string

from sklearn import mixture

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Instance, Str, List, Dict, Any
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.gaussian_1d import GaussianMixture1DOp, GaussianMixture1DView
from cytoflow.views.i_selectionview import IView
import cytoflow.utility as util

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

class GaussianMixture1DHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Channel"),
                    Item('scale'),
                    VGroup(
                    Item('num_components', 
                         editor = TextEditor(auto_set = False),
                         label = "Num\nComponents"),
                    Item('sigma',
                         editor = TextEditor(auto_set = False)),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context.previous.conditions'),
                         label = 'Group\nEstimates\nBy',
                         style = 'custom'),
                    Item('context.estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    label = "Estimation parameters",
                    show_border = False),
                    shared_op_traits)

class GaussianMixture1DPluginOp(GaussianMixture1DOp, PluginOpMixin):
    handler_factory = Callable(GaussianMixture1DHandler)
    
    # add "estimate" metadata
    num_components = util.PositiveInt(1, estimate = True)
    sigma = util.PositiveFloat(0.0, allow_zero = True, estimate = True)
    by = List(Str, estimate = True)
    
    _gmms = Dict(Any, Instance(mixture.GMM), transient = True, estimate_result = True)
    _scale = Instance(util.IScale, transient = True, estimate_result = True)
    
#     def _estimate_changed(self):
#         self.changed = "estimate_result"
    
    def default_view(self, **kwargs):
        return GaussianMixture1DPluginView(op = self, **kwargs)
    
    def clear_estimate(self):
        self._gmms.clear()

class GaussianMixture1DViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name',
                                style = 'readonly'),
                           Item('channel',
                                style = 'readonly'),
                           Item('huefacet',
                                style = 'readonly'),
                           label = "1D Mixture Model Default Plot",
                           show_border = False)),
                    VGroup(Item('subset',
                                show_label = False,
                                editor = SubsetEditor(conditions_types = "context.previous.conditions_types",
                                                      conditions_values = "context.previous.conditions_values")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('context.view_warning',
                         resizable = True,
                         visible_when = 'context.view_warning',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                 background_color = "#ffff99")),
                    Item('context.view_error',
                         resizable = True,
                         visible_when = 'context.view_error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191")))

@provides(IView)
class GaussianMixture1DPluginView(GaussianMixture1DView, PluginViewMixin):
    handler_factory = Callable(GaussianMixture1DViewHandler, transient = True)
    op = Instance(IOperation, fixed = True)

    def plot_wi(self, wi):
        if self.op.by and not wi.current_plot:
            return
        self.plot(wi.previous.result, plot_name = wi.current_plot)
        
#     def plot(self, experiment, plot_name = None, **kwargs):
#         
#         orig_op = self.op
#         
#         if self.op.name:
#             op = self.op
#             legend = True
#         else:
#             op = self.op.clone_traits()
#             op.copy_traits(self.op, transient = True)
#             op.name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
#             self.op = op
#             legend = False      
# 
#         try:
#             GaussianMixture1DView.plot(self, experiment, plot_name = plot_name, legend = legend, **kwargs)
#         finally:
#             self.op = orig_op

@provides(IOperationPlugin)
class GaussianMixture1DPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.gaussian_1d'
    operation_id = 'edu.mit.synbio.cytoflow.operations.gaussian_1d'

    short_name = "1D Mixture Model"
    menu_group = "Gates"
    
    def get_operation(self):
        return GaussianMixture1DPluginOp()
    
    def get_icon(self):
        return ImageResource('gauss_1d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
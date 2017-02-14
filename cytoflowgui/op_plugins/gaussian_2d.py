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

from sklearn import mixture

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, List, Str, Dict, Any, Instance, \
                       DelegatesTo, on_trait_change
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations import IOperation
from cytoflow.operations.gaussian_2d import GaussianMixture2DOp, GaussianMixture2DView
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

class GaussianMixture2DHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('xchannel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "X Channel"),
                    Item('ychannel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Y Channel"),
                    Item('xscale'),
                    Item('yscale'),
                    VGroup(
                    Item('num_components', 
                         editor = TextEditor(auto_set = False),
                         label = "Num\nComponents"),
                    Item('sigma',
                         editor = TextEditor(auto_set = False)),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context.previous.conditions_names'),
                         label = 'Group\nEstimates\nBy',
                         style = 'custom'),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous.conditions")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('context.do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    label = "Estimation parameters",
                    show_border = False),
                    shared_op_traits)

class GaussianMixture2DPluginOp(GaussianMixture2DOp, PluginOpMixin):
    handler_factory = Callable(GaussianMixture2DHandler)
    
    # add "estimate" metadata
    num_components = util.PositiveInt(1, estimate = True)
    sigma = util.PositiveFloat(0.0, allow_zero = True, estimate = True)
    by = List(Str, estimate = True)
    
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True, estimate_result = True)

    def default_view(self, **kwargs):
        return GaussianMixture2DPluginView(op = self, **kwargs)
    
    def estimate(self, experiment):
        GaussianMixture2DOp.estimate(self, experiment, subset = self.subset)
    
    def clear_estimate(self):
        self._gmms.clear()

class GaussianMixture2DViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('xchannel',
                                style = 'readonly'),
                           Item('ychannel',
                                style = 'readonly'),
                           label = "2D Mixture Model Default Plot",
                           show_border = False)),
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
class GaussianMixture2DPluginView(GaussianMixture2DView, PluginViewMixin):
    handler_factory = Callable(GaussianMixture2DViewHandler)
    op = Instance(IOperation, fixed = True)
    subset = DelegatesTo('op')
    by = DelegatesTo('op', status = True)
    
    @on_trait_change('by[]', post_init = True)
    def _by_changed(self):
        self.changed = "plot_names"
    
    def plot_wi(self, wi):
        self.plot(wi.previous.result, plot_name = wi.current_plot)
        
    def enum_plots_wi(self, wi):
        try:
            return self.enum_plots(wi.previous.result)
        except:
            return []
        
    def should_plot(self, changed):
        """
        Should the owning WorkflowItem refresh the plot when certain things
        change?  `changed` can be:
         - "view" -- the view's parameters changed
         - "result" -- this WorkflowItem's result changed
         - "prev_result" -- the previous WorkflowItem's result changed
         - "estimate_result" -- the results of calling "estimate" changed
        """
        if changed == "result":
            return False
        
        return True
    

@provides(IOperationPlugin)
class GaussianMixture2DPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.gaussian_2d'
    operation_id = 'edu.mit.synbio.cytoflow.operations.gaussian_2d'

    short_name = "2D Mixture Model"
    menu_group = "Gates"
    
    def get_operation(self):
        return GaussianMixture2DPluginOp()
    
    def get_icon(self):
        return ImageResource('gauss_2d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
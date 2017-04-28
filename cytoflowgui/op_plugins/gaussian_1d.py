#!/usr/bin/env python2.7
# coding: latin-1

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

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, \
                         CheckListEditor, ButtonEditor, TextEditor
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, Instance, Str, List, Dict, Any, 
                        DelegatesTo, Property, on_trait_change)
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.gaussian_1d import GaussianMixture1DOp, GaussianMixture1DView
from cytoflow.views.i_selectionview import IView
import cytoflow.utility as util

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.workflow import Changed

class GaussianMixture1DHandler(OpHandlerMixin, Controller):
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
                                                  name = 'handler.previous_conditions_names'),
                         label = 'Group\nEstimates\nBy',
                         style = 'custom'),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous.conditions")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    label = "Estimation parameters",
                    show_border = False),
                    shared_op_traits)

class GaussianMixture1DPluginOp(PluginOpMixin, GaussianMixture1DOp):
    handler_factory = Callable(GaussianMixture1DHandler)
    
    # add "estimate" metadata
    num_components = util.PositiveInt(1, estimate = True)
    sigma = util.PositiveFloat(0.0, allow_zero = True, estimate = True)
    by = List(Str, estimate = True)
    
    # bits to support the subset editor
    
    subset_list = List(ISubset, estimate = True)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change('subset_list.str', post_init = True)
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))
    
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True)
    
    def estimate(self, experiment):
        GaussianMixture1DOp.estimate(self, experiment, subset = self.subset)
        self.changed = (Changed.ESTIMATE_RESULT, self)
    
    def default_view(self, **kwargs):
        return GaussianMixture1DPluginView(op = self, **kwargs)
    
    def should_clear_estimate(self, changed):
        if changed == Changed.ESTIMATE:
            return True
        return False
    
    def clear_estimate(self):
        self._gmms = {}
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
class GaussianMixture1DViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('channel',
                                style = 'readonly'),
                           Item('by',
                                editor = TextEditor(),
                                style = 'readonly',
                                label = "Group\nBy"),
                           label = "1D Mixture Model Default Plot",
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
class GaussianMixture1DPluginView(PluginViewMixin, GaussianMixture1DView):
    handler_factory = Callable(GaussianMixture1DViewHandler, transient = True)
    op = Instance(IOperation, fixed = True)
    subset = DelegatesTo('op', transient = True)
    by = DelegatesTo('op', status = True)

    def plot_wi(self, wi):
        if wi.current_view_plot_names:
            self.plot(wi.previous.result, plot_name = wi.current_plot)
        else:
            self.plot(wi.previous.result)
        
    def enum_plots_wi(self, wi):
        try:
            return self.enum_plots(wi.previous.result)
        except:
            return []
        
    def should_plot(self, changed):
        if changed == Changed.RESULT:
            return False
        
        return True

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
    
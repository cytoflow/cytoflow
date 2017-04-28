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
import warnings

from traitsui.api import (View, Item, Controller, ButtonEditor, CheckListEditor,
                          VGroup)
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, List, Str, File, on_trait_change,
                        Property)
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations.autofluorescence import AutofluorescenceOp, AutofluorescenceDiagnosticView
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin
from cytoflowgui.workflow import Changed

class AutofluorescenceHandler(OpHandlerMixin, Controller):
    
    def default_traits_view(self):
        return View(Item('blank_file'),
                    Item('channels',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'context.previous.channels'),
                         style = 'custom'),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous.conditions",
                                                          metadata = "context.previous.metadata",
                                                          when = "'experiment' not in vars() or not experiment")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    shared_op_traits)

class AutofluorescencePluginOp(PluginOpMixin, AutofluorescenceOp):
    handler_factory = Callable(AutofluorescenceHandler)
    
    channels = List(Str, estimate = True)
    blank_file = File(filter = ["*.fcs"], estimate = True)

    @on_trait_change('channels', post_init = True)
    def _channels_changed(self):
        self.changed = (Changed.ESTIMATE, ('channels', self.channels))
        
    
    # bits to support the subset editor
    
    subset_list = List(ISubset, estimate = True)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change('subset_list.str', post_init = True)
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))

  
    
    def default_view(self, **kwargs):
        return AutofluorescencePluginView(op = self, **kwargs)
    
    def estimate(self, experiment):
        if not self.subset:
            warnings.warn("Are you sure you don't want to specify a subset "
                          "used to estimate the model?",
                          util.CytoflowOpWarning)
            
        AutofluorescenceOp.estimate(self, experiment, subset = self.subset)
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
        
    def clear_estimate(self):
        self._af_median.clear()
        self._af_stdev.clear()
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
    
    def should_apply(self, changed):
        if changed == Changed.PREV_RESULT or changed == Changed.ESTIMATE_RESULT:
            return True
        
        return False

    
    def should_clear_estimate(self, changed):
        if changed == Changed.ESTIMATE:
            return True
        
        return False
        

class AutofluorescenceViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('context.view_warning',
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
class AutofluorescencePluginView(PluginViewMixin, AutofluorescenceDiagnosticView):
    handler_factory = Callable(AutofluorescenceViewHandler)
    
    def plot_wi(self, wi):
        self.plot(wi.previous.result)

    
    def should_plot(self, changed):
        if changed == Changed.ESTIMATE_RESULT:
            return True
        
        return False
    

@provides(IOperationPlugin)
class AutofluorescencePlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.autofluorescence'
    operation_id = 'edu.mit.synbio.cytoflow.operations.autofluorescence'

    short_name = "Autofluorescence correction"
    menu_group = "Calibration"
    
    def get_operation(self):
        return AutofluorescencePluginOp()
    
    def get_icon(self):
        return ImageResource('autofluorescence')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
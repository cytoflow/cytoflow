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

import random, string, warnings

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor
from envisage.api import Plugin, contributes_to
from traits.api import provides, Callable, Str, Instance
from pyface.api import ImageResource

from cytoflow.operations import IOperation
from cytoflow.operations.binning import BinningOp, BinningView
from cytoflow.views.histogram import HistogramView
from cytoflow.views.i_selectionview import IView
import cytoflow.utility as util

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin

class BinningHandler(Controller, OpHandlerMixin):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('channel',
                         editor=EnumEditor(name='context.previous.channels'),
                         label = "Channel"),
                    Item('scale'),
                    Item('num_bins', 
                         editor = TextEditor(auto_set = False),
                         label = "Num Bins"),
                    Item('bin_width',
                         editor = TextEditor(auto_set = False),
                         label = "Bin Width"),
                    shared_op_traits)

class BinningPluginOp(PluginOpMixin, BinningOp):
    handler_factory = Callable(BinningHandler)
    
    def default_view(self, **kwargs):
        return BinningPluginView(op = self, **kwargs)

class BinningViewHandler(Controller, ViewHandlerMixin):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('channel',
                                style = 'readonly'),
                           Item('huefacet',
                                style = 'readonly'),
                           label = "Binning Default Plot",
                           show_border = False)),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "handler.context.previous.conditions")),
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
class BinningPluginView(PluginViewMixin, BinningView):
    handler_factory = Callable(BinningViewHandler)
    op = Instance(IOperation, fixed = True)
    huefacet = Str(status = True)
    huescale = util.ScaleEnum(status = True)
    
    def plot_wi(self, wi):
        self.plot(wi.previous.result)

    def plot(self, experiment, **kwargs):
    
        if self.op.name:
            op = self.op
            self.huefacet = op.name
            self.huescale = op.scale
            legend = True
        else:
            op = self.op.clone_traits()
            op.name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            self.huefacet = op.name
            legend = False      

        try:
            experiment = op.apply(experiment)
        except util.CytoflowOpError as e:
            warnings.warn(e.__str__(), util.CytoflowViewWarning)
            self.huefacet = ""
        
        HistogramView.plot(self, experiment, legend = legend, **kwargs)


@provides(IOperationPlugin)
class BinningPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.binning'
    operation_id = 'edu.mit.synbio.cytoflow.operations.binning'

    short_name = "Binning"
    menu_group = "Gates"
    
    def get_operation(self):
        return BinningPluginOp()
    
    def get_icon(self):
        return ImageResource('binning')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    
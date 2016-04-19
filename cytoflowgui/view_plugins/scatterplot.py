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
Created on Apr 23, 2015

@author: brian
'''

from traits.api import provides, Callable
from traitsui.api import View, Item, Controller, EnumEditor, VGroup
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import ScatterplotView

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.clearable_enum_editor import ClearableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin

class ScatterplotHandler(Controller, ViewHandlerMixin):
    '''
    classdocs
    '''

    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('name'),
                           Item('xchannel',
                                editor=EnumEditor(name='context.channels'),
                                label = "X Channel"),
                           Item('xscale',
                                label = "X Scale"),
                           Item('ychannel',
                                editor=EnumEditor(name='context.channels'),
                                label = "Y Channel"),
                           Item('yscale',
                                label = "Y Scale"),
                           Item('xfacet',
                                editor=ClearableEnumEditor(name='context.conditions_names'),
                                label = "Horizontal\nFacet"),
                           Item('yfacet',
                                editor=ClearableEnumEditor(name='context.conditions_names'),
                                label = "Vertical\nFacet"),
                           Item('huefacet',
                                editor=ClearableEnumEditor(name='context.conditions_names'),
                                label="Color\nFacet")),
                    VGroup(Item('subset',
                                show_label = False,
                                editor = SubsetEditor(experiment = "context.result")),
                                show_border = True,
                                show_labels = False),
                           Item('warning',
                                resizable = True,
                                visible_when = 'warning',
                                editor = ColorTextEditor(foreground_color = "#000000",
                                                         background_color = "#ffff99")),
                           Item('error',
                                resizable = True,
                                visible_when = 'error',
                                editor = ColorTextEditor(foreground_color = "#000000",
                                                         background_color = "#ff9191")),
                           show_labels = False))


class ScatterplotPluginView(ScatterplotView, PluginViewMixin):
    handler_factory = Callable(ScatterplotHandler)

@provides(IViewPlugin)
class ScatterplotPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.scatterplot'
    view_id = 'edu.mit.synbio.cytoflow.view.scatterplot'
    short_name = "Scatter Plot"
    
    def get_view(self):
        return ScatterplotPluginView()
    
    def get_icon(self):
        return ImageResource('scatterplot')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self

        
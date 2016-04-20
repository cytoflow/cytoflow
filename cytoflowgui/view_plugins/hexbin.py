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
from traitsui.api import View, Item, Controller, EnumEditor, Heading
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow import HexbinView

from cytoflowgui.subset_editor import SubsetEditor
from cytoflowgui.clearable_enum_editor import ClearableEnumEditor
from cytoflowgui.view_plugins.i_view_plugin \
    import IViewPlugin, VIEW_PLUGIN_EXT, ViewHandlerMixin, PluginViewMixin

class HexbinHandler(Controller, ViewHandlerMixin):
    '''
    classdocs
    '''

    def default_traits_view(self):
        return View(Heading('THE HEXBIN PLUGIN IS BROKEN.'))
#                     Item('name'),
#                     Item('xchannel',
#                          editor=EnumEditor(name='context.channels'),
#                          label = "X Channel"),
#                     Item('xscale',
#                          label = "X Scale"),
#                     Item('ychannel',
#                          editor=EnumEditor(name='context.channels'),
#                          label = "Y Channel"),
#                     Item('yscale',
#                          label = "Y Scale"),
#                     Item('xfacet',
#                          editor=ClearableEnumEditor(name='context.conditions_names'),
#                          label = "Horizontal\nFacet"),
#                     Item('object.yfacet',
#                          editor=ClearableEnumEditor(name='context.conditions_names'),
#                          label = "Vertical\nFacet"),
#                     Item('object.huefacet',
#                          editor=ClearableEnumEditor(name='context.conditions_names'),
#                          label="Color\nFacet"),
#                     Item('_'),
#                     Item('subset',
#                          label="Subset",
#                          editor = SubsetEditor(experiment = "context.result")))

class HexbinPluginView(HexbinView, PluginViewMixin):
    handler_factory = Callable(HexbinHandler)

@provides(IViewPlugin)
class HexbinPlugin(Plugin):
    """
    classdocs
    """

    id = 'edu.mit.synbio.cytoflowgui.view.hexbin'
    view_id = 'edu.mit.synbio.cytoflow.view.hexbin'
    short_name = "HexBin"

    def get_view(self):
        return HexbinPluginView()
    
    def get_icon(self):
        return ImageResource('hexbin')

    @contributes_to(VIEW_PLUGIN_EXT)
    def get_plugin(self):
        return self
        
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

"""
Created on Mar 15, 2015

@author: brian
"""

from traits.api import Interface, Str, HasTraits, Property, Instance, List
from traitsui.api import Handler, Group, Item
from cytoflowgui.workflow import WorkflowItem
from cytoflowgui.color_text_editor import ColorTextEditor

VIEW_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.view_plugins'

class IViewPlugin(Interface):
    """
    
    Attributes
    ----------
    
    id : Str
        The envisage ID used to refer to this plugin
        
    view_id : Str
        Same as the "id" attribute of the IView this plugin wraps
        Prefix: edu.mit.synbio.cytoflowgui.view
        
    short_name : Str
        The view's "short" name - for menus, toolbar tips, etc.
    """
    
    view_id = Str
    short_name = Str

    def get_view(self):
        """Return an IView instance that this plugin wraps"""
        
    
    def get_icon(self):
        """
        Returns an icon for this plugin
        """
        
class PluginViewMixin(HasTraits):
    handler = Instance(Handler, transient = True)
    warning = Str(transient = True)
    error = Str(transient = True)
    
shared_view_traits = Group(Item('object.warning',
                                label = 'Warning',
                                visible_when = 'object.warning',
                                editor = ColorTextEditor(foreground_color = "#000000",
                                                         background_color = "#ffff99",
                                                         word_wrap = True)),
                           Item('object.error',
                                 label = 'Error',
                                 visible_when = 'object.error',
                                 editor = ColorTextEditor(foreground_color = "#000000",
                                                          background_color = "#ff9191",
                                                          word_wrap = True)))

class ViewHandlerMixin(HasTraits):
    """
    Common bits useful for View wrappers.
    """
     
    channels = Property(List, depends_on = 'wi.channels')
    conditions = Property(List, depends_on = 'wi.conditions')
    
    wi = Instance(WorkflowItem)

    # MAGIC: provides dynamically updated values for the "channels" trait
    def _get_channels(self):
        """
        doc
        """
        if self.wi and self.wi.result and self.wi.result.channels:
            return self.wi.result.channels
        else:
            return []
         
    # MAGIC: provides dynamically updated values for the "conditions" trait
    def _get_conditions(self):
        """
        doc
        """
        ret = [""]
        if self.wi and self.wi.result and self.wi.result.conditions:
            ret.extend(self.wi.result.conditions.keys())
        return ret


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

from traits.api import (Interface, Str, HasTraits, Instance, Event, 
                        List, Property, on_trait_change)
from traitsui.api import Handler

from cytoflowgui.subset import ISubset
from cytoflowgui.workflow import Changed
from cytoflowgui.workflow_item import WorkflowItem

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
    
    # transmit some change back to the workflow
    changed = Event
    
    # plot names
    plot_names = List(Str, status = True)
    
    subset_list = List(ISubset)
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
 
    @on_trait_change('subset_list.str')
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.VIEW, (self, 'subset_list', self.subset_list))  
            
    def should_plot(self, changed):
        """
        Should the owning WorkflowItem refresh the plot when certain things
        change?  `changed` can be:
         - Changed.VIEW -- the view's parameters changed
         - Changed.RESULT -- this WorkflowItem's result changed
         - Changed.PREV_RESULT -- the previous WorkflowItem's result changed
         - Changed.ESTIMATE_RESULT -- the results of calling "estimate" changed
        """
        return True
    
    def plot_wi(self, wi):
        if wi.current_view_plot_names:
            self.plot(wi.result, plot_name = wi.current_plot)
        else:
            self.plot(wi.result)
            
    def enum_plots_wi(self, wi):
        try:
            return self.enum_plots(wi.result)
        except:
            return []
            

class ViewHandlerMixin(HasTraits):
    """
    Useful bits for view handlers. 
    """
    
    context = Instance(WorkflowItem)
    
    conditions_names = Property(depends_on = "context.conditions")
    previous_conditions_names = Property(depends_on = "context.previous.conditions")
    statistics_names = Property(depends_on = "context.statistics")
    
    # MAGIC: gets value for property "conditions_names"
    def _get_conditions_names(self):
        if self.context and self.context.conditions:
            return self.context.conditions.keys()
        else:
            return []
    
    # MAGIC: gets value for property "previous_conditions_names"
    def _get_previous_conditions_names(self):
        if self.context and self.context.previous and self.context.previous.conditions:
            return self.context.previous.conditions.keys()
        else:
            return []
        
    # MAGIC: gets value for property "statistics_names"
    def _get_statistics_names(self):
        if self.context and self.context.statistics:
            return self.context.statistics.keys()
        else:
            return []

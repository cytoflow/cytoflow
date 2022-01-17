#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflowgui.experiment_pane_model
--------------------------------

The classes that provide the model for the `ExperimentBrowserDockPane`.
"""

from traits.api import Instance, Str, Tuple
from traitsui.api import TreeEditor, TreeNodeObject, ObjectTreeNode

from .workflow import WorkflowItem


class WorkflowItemNode(TreeNodeObject):
    """A tree node for the Experiment"""
    
    wi = Instance(WorkflowItem)
    label = 'WorkflowItem'

    def tno_get_label(self, _):
        return self.label
    
    def tno_allows_children(self, node):
        return True
 
    def tno_has_children(self, node):
        return True
    
    def tno_get_menu(self, _):
        return False
    
    def tno_get_children(self, _):
        return [ChannelsNode(wi = self.wi),
                ConditionsNode(wi = self.wi),
                StatisticsNode(wi = self.wi)]
    

class ChannelsNode(TreeNodeObject):
    """A tree node for the group of channels"""
    
    wi = Instance(WorkflowItem)
    label = "Channels"
    
    def tno_get_label(self, node):
        return self.label
     
    def tno_allows_children(self, node):
        return True
 
    def tno_has_children(self, node):
        return True
    
    def tno_get_menu(self, _):
        return False
    
    def tno_get_icon(self, node, is_expanded):
        return "@icons:list_node"
    
    def tno_get_children(self, _):
        return [ChannelNode(wi = self.wi,
                            channel = x) for x in self.wi.channels]

     
class ChannelNode(TreeNodeObject):
    """A tree node for a single channel"""
    
    wi = Instance(WorkflowItem)
    """The `WorkflowItem` that this channel is part of"""
    
    channel = Str()    
    
    def tno_get_label(self, _):
        return self.channel
    
    def tno_allows_children(self, _):
        return True
    
    def tno_has_children(self, _):
        return True
    
    def tno_get_menu(self, _):
        return False
    
    def tno_get_icon(self, node, is_expanded):
        return "@icons:int_node"
    
    def tno_get_children(self, _):
        return [StringNode(name = k, value = str(self.wi.metadata[self.channel][k])) 
                           for k in self.wi.metadata[self.channel].keys()]

class ConditionsNode(TreeNodeObject):
    """A tree node for all the conditions"""
    
    wi = Instance(WorkflowItem)
    label = "Conditions"
    
    def tno_get_label(self, _):
        return self.label
    
    def tno_allows_children(self, node):
        return True
 
    def tno_has_children(self, node):
        return True
    
    def tno_get_menu(self, _):
        return False

    def tno_get_icon(self, node, is_expanded):
        return "@icons:set_node"

    def tno_get_children(self, _):
        return [ConditionNode(wi = self.wi,
                              condition = x) for x in self.wi.conditions.keys()]
    

class ConditionNode(TreeNodeObject):
    """A tree node for a single condition"""
    
    wi = Instance(WorkflowItem)
    """The `WorkflowItem` that this condition is part of"""
    
    condition = Str()    
    
    def tno_get_label(self, _):
        return self.condition
    
    def tno_allows_children(self, _):
        return True
    
    def tno_has_children(self, _):
        return True
    
    def tno_get_menu(self, _):
        return False
    
    def tno_get_icon(self, node, is_expanded):
        return "@icons:string_node"
    
    def tno_get_children(self, _):
#         condition = self.wi.conditions[self.condition]
#         values = condition.sort_values()
#         dtype = pd.Series(list(values)).dtype
#         if dtype.kind == 'b':
#             ret = [StringNode(name = 'Type',
#                               value = 'boolean')]
#         elif dtype.kind in "ifu":
#             ret = [StringNode(name = 'Type',
#                               value = 'numeric'),
#                    StringNode(name = 'Values',
#                               value = ', '.join([str(x) for x in values]))]
#         elif dtype.kind in "OSU":
#             ret = [StringNode(name = 'Type',
#                               value = 'categorical'),
#                    StringNode(name = 'Values',
#                               value = ', '.join(values))]
            
        return [StringNode(name = k, value = str(self.wi.metadata[self.condition][k])) 
                           for k in self.wi.metadata[self.condition].keys()]
                    

class StatisticsNode(TreeNodeObject):
    """A tree node for all the statistics"""
    
    wi = Instance(WorkflowItem)
    label = "Statistics"
    
    def tno_get_label(self, _):
        return self.label
    
    def tno_allows_children(self, node):
        return True
 
    def tno_has_children(self, node):
        return True
    
    def tno_get_menu(self, _):
        return False
    
    def tno_get_icon(self, node, is_expanded):
        return "@icons:dict_node"
    
    def tno_get_children(self, _):
        return [StatisticNode(wi = self.wi,
                              statistic = x) for x in self.wi.statistics.keys()]
        
    
class StatisticNode(TreeNodeObject):
    """A tree node for a single statistic"""
    
    wi = Instance(WorkflowItem)
    """The `WorkflowItem` that this condition is part of"""
    
    statistic = Tuple()   
    
    def tno_get_label(self, _):
        return str(self.statistic)
    
    def tno_allows_children(self, _):
        return True
    
    def tno_has_children(self, _):
        return True
    
    def tno_get_menu(self, _):
        return False
    
    def tno_get_icon(self, node, is_expanded):
        return "@icons:other_node"
    
    def tno_get_children(self, _):
        statistic = self.wi.statistics[self.statistic]
        ret = [StringNode(name = 'Operation',
                          value = self.statistic[0]),
               StringNode(name = 'Name',
                          value = self.statistic[1])]
                
        if statistic.index.nlevels == 1:
            ret.append(StringNode(name = 'Facet Name',
                                  value = str(statistic.index.names[0])))
            ret.append(StringNode(name = 'Facet Levels',
                                  value = ", ".join([str(x) for x in statistic.index.values])))
        else:
            for i, name in enumerate(statistic.index.names):
                ret.append(StringNode(name = 'Facet ' + str(i),
                                      value = name))
                ret.append(StringNode(name = 'Facet ' + str(i) + ' Levels',
                                      value = ', '.join([str(x) for x in statistic.index.levels[i]])))
            
        return ret
    
class StringNode(TreeNodeObject):
    """ 
    A tree node for strings
    """

    #: Name of the value
    name = Str()

    #: User-specified override of the default label
    label = Str()

    #: The value itself
    value = Str()

    def tno_allows_children(self, node):
        return False

    def tno_has_children(self, node):
        return False
    
    def tno_get_menu(self, _):
        return False

    def tno_get_icon(self, node, is_expanded):
        return "@icons:complex_node"

    def tno_get_label(self, node):
        """ Gets the label to display for a specified object.
        """
        if self.label != "":
            return self.label

        if self.name == "":
            return self.format_value(self.value)

        return "%s: %s" % (self.name, self.format_value(self.value))

    def format_value(self, value):
        """ Returns the formatted version of the value.
        """
        return repr(value)
            
    
experiment_tree_editor = TreeEditor(
    editable = False,
    auto_open = 2,
    hide_root = True,
    lines_mode = "off",
    nodes = [
        ObjectTreeNode(
            node_for = [
                WorkflowItemNode,
                ChannelsNode,
                ChannelNode,
                ConditionsNode,
                ConditionNode,
                StatisticsNode,
                StatisticNode,
                StringNode
            ],
            rename = False,
            rename_me = False,
            copy = False,
            delete = False,
            delete_me = False)])

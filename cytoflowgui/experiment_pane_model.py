#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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

from traits.api import Instance, Str
from traitsui.api import TreeEditor, TreeNodeObject, ObjectTreeNode
from traitsui.value_tree import StringNode, BoolNode, IntNode, FloatNode, NoneNode

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
    
    def tno_get_children(self, _):
        return [ChannelsNode(wi = self.wi)]
    

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
    
    def tno_get_children(self, _):
        return [ChannelNode(wi = self.wi,
                            channel = x) for x in self.wi.channels]

     
class ChannelNode(TreeNodeObject):
    """A tree node for a single channel"""
    
    wi = Instance(WorkflowItem)
    """The experiment that this channel is part of"""
    
    channel = Str()    
    
    def tno_get_label(self, _):
        return self.channel
    
    def tno_allows_children(self, _):
        return True
    
    def tno_has_children(self, _):
        return True
    
    def tno_get_children(self, _):
        return [StringNode(parent = self,
                           name = 'fcs_name',
                           value = self.wi.metadata[self.channel]['fcs_name']),
                FloatNode(parent = self,
                          name = 'range',
                          value = self.wi.metadata[self.channel]['range'])]

class ConditionNode(TreeNodeObject):
    pass

class StatisticNode(TreeNodeObject):
    pass

    
experiment_tree_editor = TreeEditor(
    editable = False,
    auto_open = 2,
    hide_root = True,
    nodes = [
        ObjectTreeNode(
            node_for = [
                WorkflowItemNode,
                ChannelsNode,
                ChannelNode,
                ConditionNode,
                StatisticNode,
                StringNode,
                BoolNode,
                IntNode,
                FloatNode,
                NoneNode
            ],
            rename = False,
            rename_me = False,
            copy = False,
            delete = False,
            delete_me = False)])

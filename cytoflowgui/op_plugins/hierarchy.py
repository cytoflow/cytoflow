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


'''
Hierarchical Gating
-------------------

Convert a hierarchical (binary) gating strategy into a categorical condition.

Hierarchical gating strategies are quite common when doing manual gating.
For example, an 8-stain panel can separate monocytes into macrophages, B cells,
NK cells, NKT cells, T cells, DCs, and neutrophils -- but then, because these
states are mutually exclusive, a reasonable question is "how much of each are there?"
``Cytoflow`` can define these gates, but because it does not have any 
concept of nested gates, plotting and analyzing this gating strategy can be
challenging.

The ``Hierarchical Gating`` operation converts a list of gates into a categorical 
variable to enable straightforward analysis. For example, monocytes stained with CD64, 
CD3 and CD19 can differentiate between macrophages and B cells. A user
defines a threshold gate to separate CD64+ cells (macrophages) from the
rest of the events, then they use a polygon gate to distinguish the CD19+/CD3-
cells (B cells) from everything else. The ``Hierarchical Gating`` operation can take these two gates
and create a categorical condition with the values ``Macrophages``, ``B_Cells``,
and ``Unknown``.

The operation is set up by providing a list of conditions, values for those
conditions, and the category that condition indicates. Figuring out an 
event's category is done by evaluating the hierarchical gates **in order.**
For each event, the first condition/value pair is considered. If that event
has that value, its new category is set accordingly. If not, then the next
gate in the list is considered. If the event is a member in none of the gates,
it receives the category listed in the ``Default`` attribute.
    
.. object:: Name

        The name of the new condition that this operation creates.

.. object:: Gates

        The ordered list of gates that implement the gating hierarchy. 
        For each, you need to specify:
        
        * The *name* of the pre-existing condition
          
        * The *value* that the condition has to have to indicate membership
          in this class.
          
        * The name of the new *category*.
        
.. object:: Default 

        The name that unclassified events will have in the new categorical
        condition.
    
'''

from natsort import natsorted

from traits.api import provides, List, Str, Property, Event
from traitsui.api import View, Item, EnumEditor, VGroup, TextEditor, Controller, ButtonEditor
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..workflow.operations import HierarchyWorkflowOp, HierarchyGate
from ..editors import InstanceHandlerEditor, VerticalListEditor


from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin

class GateHandler(Controller):
    values = Property(List, observe = 'model.gate')
    gate_view = View(VGroup(Item('gate',
                                 editor = EnumEditor(name = 'context_handler.conditions')),
                            Item('value',
                                 editor = EnumEditor(name = 'handler.values')),
                            Item('category',
                                 editor = TextEditor(auto_set = False,
                                                     placeholder = "None")),
                            Item('_')))

    def _get_values(self):
        if self.model.gate and self.info.context_handler.context.conditions:
            return natsorted(self.info.context_handler.context.conditions[self.model.gate].unique())
        else:
            return []
        
class HierarchyHandler(OpHandler):
    add_gate = Event
    remove_gate = Event
    conditions = Property(List(Str), observe = 'context.conditions')
    
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             VGroup(Item('gates_list',
                         editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'gate_view',
                                                                                    handler_factory = GateHandler),
                                                     style = 'custom',
                                                     mutable = False)),
             Item('handler.add_gate',
                  editor = ButtonEditor(value = True,
                                        label = "Add a gate"),
                  show_label = False),
             Item('handler.remove_gate',
                  editor = ButtonEditor(value = True,
                                        label = "Remove a gate")),
             show_labels = False),
             Item('default',
                  editor = TextEditor(auto_set = False)),
             shared_op_traits_view) 
        
    # MAGIC: called when add_channel is set
    def _add_gate_fired(self):
        self.model.gates_list.append(HierarchyGate())
        
    def _remove_gate_fired(self):
        if self.model.gates_list:
            self.model.gates_list.pop()   
            
    def _get_conditions(self):
        if self.context and self.context.conditions:
            return list(self.context.conditions.keys())
        else:
            return []
        

@provides(IOperationPlugin)
class HierarchyPlugin(Plugin, PluginHelpMixin):
    id = 'cytoflowgui.op_plugins.hierarchy'
    operation_id = 'cytoflow.operations.hierarchy'
    view_id = None

    short_name = "Gate\nHierarchy"
    name = "Hierarchical Gating"
    menu_group = "Gates"
    
    def get_operation(self):
        return HierarchyWorkflowOp()
    
    def get_handler(self, model, context):
        return HierarchyHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('hierarchy')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]


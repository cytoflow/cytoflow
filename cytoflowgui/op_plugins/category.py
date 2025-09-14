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
Categorical Gating
------------------

Convert a binary gating strategy into a categorical condition.

Binary gating strategies are quite common while doing manual gating.
For example, a gating strategy might be "if a monocyte is CD64-, CD19+, 
and CD3-, then it is a B cell; if it is CD64+, it is a macrophage". 
Analyzing these data sets is often easier if one can specify a set of
gate memberships, for example making a categorical variable with the
values ``B_Cell`` and ``Macrophage``.

If the gating strategy is strictly hierarchical, then you can use 
``Hierarchical Gating`` operation to accomplish this easily. For more 
complicated situations, there is ``Categorical Gating``. This operation
is configured with a list of subsets and the name to give each subset.
**These subsets must be mutually exclusive,** a requirement which is 
enforced by the operation. A new categorical variable is then created,
whose categories are the names and each of which is applied to events
in the category's subset.

Any event that is in none of the subsets is set to a default value, which
defaults to ``Unknown``. 
    
.. object:: Name

        The name of the new condition that this operation creates.

.. object:: Subsets

        The mutually exclusive subsets that will be assigned categories. For 
        each, you need to specify:
        
        * The *name* of the new category
          
        * The *subset* of events that should be assigned that category.
                  
.. object:: Default 

        The name that unclassified events will have in the new categorical
        condition.
    
'''

from traits.api import provides, List, Property, Event
from traitsui.api import View, Item, VGroup, TextEditor, Controller, ButtonEditor, Label
from envisage.api import Plugin
from pyface.api import ImageResource  # @UnresolvedImport

from ..workflow.operations import CategoryWorkflowOp, CategoryOpSubset
from ..editors import InstanceHandlerEditor, VerticalListEditor, SubsetListEditor
from ..subset_controllers import subset_handler_factory

from .i_op_plugin import IOperationPlugin, OP_PLUGIN_EXT
from .op_plugin_base import OpHandler, shared_op_traits_view, PluginHelpMixin

class CategoryOpSubsetHandler(Controller):
    previous_conditions = Property(List)
    
    subset_view = View(VGroup(Item('subset_list',
                                   show_label = False,
                                   editor = SubsetListEditor(conditions = "handler.previous_conditions",
                                                             editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                            handler_factory = subset_handler_factory))),
                              show_border = False,
                              show_labels = False),
                       Item('category',
                            editor = TextEditor(auto_set = False,
                                                placeholder = "None")),
                       Item('_'))

    def _get_previous_conditions(self):
        if self.info.context_handler.context.previous_wi:
            return self.info.context_handler.context.previous_wi.conditions
        else:
            return []

        
class CategoryHandler(OpHandler):
    add_subset = Event
    remove_subset = Event
    
    operation_traits_view = \
        View(Item('name',
                  editor = TextEditor(auto_set = False,
                                      placeholder = "None")),
             Item('_'),
             VGroup(Item('subsets_list',
                         editor = VerticalListEditor(editor = InstanceHandlerEditor(view = 'subset_view',
                                                                                           handler_factory = CategoryOpSubsetHandler),
                                                     style = 'custom',
                                                     mutable = False)),
                    Item('handler.add_subset',
                         editor = ButtonEditor(value = True,
                                               label = "Add a category"),
                         show_label = False),
                    Item('handler.remove_subset',
                         editor = ButtonEditor(value = True,
                                               label = "Remove a category")),
                    show_labels = False),
             Item('default',
                  editor = TextEditor(auto_set = False)),
             shared_op_traits_view) 
        
    # MAGIC: called when add_channel is set
    def _add_subset_fired(self):
        self.model.subsets_list.append(CategoryOpSubset(context = self.context))
        
    def _remove_subset_fired(self):
        if self.model.subsets_list:
            self.model.subsets_list.pop()   
        

@provides(IOperationPlugin)
class CategoryPlugin(Plugin, PluginHelpMixin):
    id = 'cytoflowgui.op_plugins.category'
    operation_id = 'cytoflow.operations.category'
    view_id = None

    short_name = "Gate\nCategories"
    name = "Categorical Gating"
    menu_group = "Gates"
    
    def get_operation(self):
        return CategoryWorkflowOp()
    
    def get_handler(self, model, context):
        return CategoryHandler(model = model, context = context)

    def get_icon(self):
        return ImageResource('category')
    
    plugin = List(contributes_to = OP_PLUGIN_EXT)
    def _plugin_default(self):
        return [self]


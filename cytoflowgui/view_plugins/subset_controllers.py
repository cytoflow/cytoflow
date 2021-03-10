#!/usr/bin/env python3.4
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

from traitsui.api import Controller, View, HGroup, Item, CheckListEditor

from ..editors import ValuesBoundsEditor

from cytoflowgui.workflow.subset import BoolSubset, CategorySubset, RangeSubset

class BoolSubsetHandler(Controller):
    
    def subset_view(self):
        return View(HGroup(Item('selected_t',
                                label = self.model.name + "+"), 
                           Item('selected_f',
                                label = self.model.name + "-")))
        
        
class CategorySubsetHandler(Controller):
    
    def subset_view(self):
        return View(Item('selected',
                         label = self.model.name,
                         editor = CheckListEditor(name = 'values',
                                                  cols = 2),
                         style = 'custom'))
        
        
class RangeSubsetHandler(Controller):
    
    def subset_view(self):
        return View(Item('high',
                         label = self.model.name,
                         editor = ValuesBoundsEditor(
                                     name = 'values',
                                     low_name = 'low',
                                     high_name = 'high',
                                     format = '%g',
                                     auto_set = False)))
        
        
def subset_handler_factory(model):
    if isinstance(model, BoolSubset):
        return BoolSubsetHandler(model)
    elif isinstance(model, CategorySubset):
        return CategorySubsetHandler(model)
    elif isinstance(model, RangeSubset):
        return RangeSubsetHandler(model)
    
    
    
    
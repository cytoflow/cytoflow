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
cytoflowgui.editors.ext_enum_editor
-----------------------------------

A `traitsui.editors.enum_editor.EnumEditor` that allows **_names** to be extended with
**extra_items** in the factory.

"""

from traits.api import Dict

from traitsui.qt4.enum_editor import SimpleEditor as _EnumEditor
from traitsui.editors.enum_editor import EnumEditor

class _ExtendableEnumEditor(_EnumEditor):

    def _get_names ( self ):
        """ Gets the current set of enumeration names.
        """        
        if self._object is None:
            return self.factory._names + list(self.factory.extra_items.keys())
        else:
            return self._names + list(self.factory.extra_items.keys())
    
    def _get_mapping ( self ):
        """ Gets the current mapping.
        """
        if self._object is None:
            m = dict(self.factory._mapping)
        else:
            m = self._mapping
            
        m.update(self.factory.extra_items)

        return m
    
    def _get_inverse_mapping ( self ):
        """ Gets the current inverse mapping.
        """
        
        if self._object is None:
            m = dict(self.factory._inverse_mapping)
        else:
            m = dict(self._inverse_mapping)
            
        m.update({v: k for k, v in list(self.factory.extra_items.items())})
        
        return m
        
class ExtendableEnumEditor(EnumEditor):
    
    extra_items = Dict
    """The extra items for the enum, beyond what's in **names**"""
        
    def _get_simple_editor_class(self):
        """ Returns the editor class to use for "simple" style views.
        The default implementation tries to import the SimpleEditor class in the
        editor file in the backend package, and if such a class is not to found
        it returns the SimpleEditor class defined in editor_factory module in
        the backend package.
        """
        return _ExtendableEnumEditor

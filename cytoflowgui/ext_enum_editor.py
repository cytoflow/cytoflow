'''
Created on Apr 16, 2016

@author: brian
'''

from traits.api import Dict

from traitsui.qt4.enum_editor import SimpleEditor as _EnumEditor
from traitsui.editors.enum_editor import EnumEditor

class _ExtendableEnumEditor(_EnumEditor):

    def _get_names ( self ):
        """ Gets the current set of enumeration names.
        """        
        if self._object is None:
            return self.factory._names + self.factory.extra_items.keys()
        else:
            return self._names + self.factory.extra_items.keys()
    
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
            
        m.update({v: k for k, v in self.factory.extra_items.items()})
        
        return m
        
class ExtendableEnumEditor(EnumEditor):
    
    extra_items = Dict
        
    def _get_simple_editor_class(self):
        """ Returns the editor class to use for "simple" style views.
        The default implementation tries to import the SimpleEditor class in the
        editor file in the backend package, and if such a class is not to found
        it returns the SimpleEditor class defined in editor_factory module in
        the backend package.
        """
        return _ExtendableEnumEditor

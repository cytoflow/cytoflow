'''
Created on Jan 16, 2021

@author: brian
'''

from pyface.qt import QtGui

from traitsui.qt4.enum_editor import BaseEditor as BaseEnumerationEditor
from traitsui.editor_factory import EditorWithListFactory
from traitsui.qt4.constants import ErrorColor

class _TabListEditor(BaseEnumerationEditor):
    
    def init(self, parent):        
        super(_TabListEditor, self).init(parent)
        
        self.control = QtGui.QTabBar()
        self.control.setDocumentMode(True)  
        for name in self.names:
            self.control.addTab(str(name))
            
        self.control.currentChanged.connect(self.update_object)


    def update_editor(self):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        try:
            index = self.names.index(self.inverse_mapping[self.value])
            self.control.setCurrentIndex(index)
        except:
            self.control.setCurrentIndex(0)
            self.update_object(0)
    
    def update_object(self, idx):
        """ Handles a notebook tab being "activated" (i.e. clicked on) by the
            user.
        """
        if idx >= 0 and idx < len(self.names):
            name = self.names[idx]
            self.value = self.mapping[str(name)]
            
    def rebuild_editor(self):
        self.control.blockSignals(True)
        
        while self.control.count() > 0:
            self.control.removeTab(0)
             
        for name in self.names:
            self.control.addTab(str(name))
            
        self.control.blockSignals(False)
        self.update_editor()
        
    def error(self, excp):
        """ Handles an error that occurs while setting the object's trait value.
        """
        self._set_background(ErrorColor)
        
        
# editor factory
class TabListEditor(EditorWithListFactory):
    def _get_custom_editor_class(self):
        return _TabListEditor

        
'''
Created on Oct 2, 2015

@author: brian
'''

from pyface.qt import QtCore, QtGui
from traitsui.editors.api import TextEditor
from traitsui.qt4.editor_factory import ReadonlyEditor

# editor factory
class ColorTextEditor(TextEditor):
    pass


class ColorTextReadonlyEditor (ReadonlyEditor):
    """ Read-only style of text editor, which displays a read-only text field.
    """

    def init(self, parent):
        super(ReadonlyEditor, self).init(parent)

        if self.factory.readonly_allow_selection:
            flags = (self.control.textInteractionFlags() |
                QtCore.Qt.TextSelectableByMouse)
            self.control.setTextInteractionFlags(flags)

    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------

    def update_editor ( self ):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        new_value = self.str_value

        if self.factory.password:
            new_value = '*' * len(new_value)

        self.control.setText(new_value)
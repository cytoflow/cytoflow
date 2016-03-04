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

'''
Created on Nov 23, 2015

@author: brian
'''
from __future__ import absolute_import

from traits.api import Str, Range, Enum, Property, Trait, Unicode, List, \
                       on_trait_change
from traitsui.view import View
from traitsui.ui_traits import AView, Image
from traitsui.editor_factory import EditorFactory
from traitsui.editor import Editor

from pyface.qt import QtCore, QtGui


class ToggleButtonEditorFactory ( EditorFactory ):
    """ 
    Editor factory for toggle buttons.  Stolen line-for-line from the button editor. 
    """

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # Value to set when the button is clicked
    value = Property

    # Optional label for the button
    label = Str

    # The name of the external object trait that the button label is synced to
    label_value = Str

    # (Optional) Image to display on the button
    image = Image

    #---------------------------------------------------------------------------
    #  Implementation of the 'value' property:
    #---------------------------------------------------------------------------
# 
#     def _get_value ( self ):
#         return self._value
# 
#     def _set_value ( self, value ):
#         self._value = value
#         if isinstance(value, basestring):
#             try:
#                 self._value = int( value )
#             except:
#                 try:
#                     self._value = float( value )
#                 except:
#                     pass

    #---------------------------------------------------------------------------
    #  Initializes the object:
    #---------------------------------------------------------------------------

    def __init__ ( self, **traits ):
        self._value = 0
        super( ToggleButtonEditorFactory, self ).__init__( **traits )
        
        
class ToggleButtonEditor(Editor):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    # The button label
    label = Unicode

    #---------------------------------------------------------------------------
    #  Finishes initializing the editor by creating the underlying toolkit
    #  widget:
    #---------------------------------------------------------------------------

    def init ( self, parent ):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        label = self.factory.label or self.item.get_label(self.ui)

        self.control = QtGui.QPushButton(self.string_value(label))
        self.control.setAutoDefault(False)
        self.control.setCheckable(True)

        self.sync_value(self.factory.label_value, 'label', 'from')
        self.control.toggled.connect(self.update_object)
        self.set_tooltip()

    def _label_changed(self, label):
        self.control.setText(self.string_value(label))

    def update_object(self):
        """ Handles the user clicking the button by setting the factory value
            on the object.
        """
        
        self.value = self.control.toggled()

    def update_editor(self):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        self.control.toggled = self.value
        
        
if __name__ == '__main__':

    from traits.api import HasTraits, Bool
    from traitsui.api import View, Group, Item
    
    class TestClass(HasTraits):
        b = Bool
        
        traits_view = View(Item(name = 'b',
                                editor = ToggleButtonEditorFactory()))
        
    test = TestClass()
    test.configure_traits()
        
        
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
cytoflowgui.editors.toggle_button
---------------------------------

A button that can be toggled off and on.
"""

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import Str, Property
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor

from pyface.qt import QtGui

        
class _ToggleButton(Editor):

    #---------------------------------------------------------------------------
    #  Trait definitions:
    #---------------------------------------------------------------------------

    label = Str
    """The button label"""

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
        self.control.setChecked(self.value)

    # MAGIC - called when label is updated
    def _label_changed(self, label):
        self.control.setText(self.string_value(label))

    def update_object(self):
        """ Handles the user clicking the button by setting the factory value
            on the object.
        """
        
        self.value = self.control.isChecked()

    def update_editor(self):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        self.control.setChecked(self.value)
        
class ToggleButtonEditor(BasicEditorFactory):
    """ 
    Editor factory for toggle buttons.
    """

    klass = _ToggleButton

    value = Property
    """Value to set when the button is clicked"""

    label = Str
    """Optional label for the button"""
 
    label_value = Str
    """The name of the external object trait that the button label is synced to"""
 
        
if __name__ == '__main__':

    from traits.api import HasTraits, Bool, String
    from traitsui.api import View, Item
    
    class TestClass(HasTraits):
        b = Bool(True)
        b_str = String("teststring")
        
        traits_view = View(Item(name = 'b',
                                label = "boooool",
                                show_label = False,
                                editor = ToggleButtonEditor(label_value = "b_str")))
        
    test = TestClass()
    test.configure_traits()
    print(test.b)
        
        
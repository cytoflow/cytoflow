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

"""
cytoflowgui.editors.color_text_editor
-------------------------------------

A `traitsui.editors.text_editor.TextEditor`
that allows you to set the foreground and background color
of the text.
"""

from pyface.qt import QtGui, QtCore
from traitsui.qt.editor_factory import ReadonlyEditor
from traitsui.api import BasicEditorFactory
from traits.api import Color, Instance, Str, Undefined

class _ColorTextEditor(ReadonlyEditor):

    _palette = Instance(QtGui.QPalette)
    _foreground_color = Color
    _background_color = Color

    def init(self, parent):
        super(_ColorTextEditor, self).init(parent)
 
        flags = (self.control.textInteractionFlags() |
                 QtCore.Qt.TextSelectableByMouse)
        self.control.setTextInteractionFlags(flags)

        fg_color = self.factory.foreground_color
        if fg_color[0:1] == '.':
            if getattr(self.value, fg_color[1:], Undefined) is not Undefined:
                self.sync_value(fg_color[1:], '_foreground_color', 'from')
        else:
            self._foreground_color = fg_color
            
        bg_color = self.factory.background_color
        if bg_color[0:1] == '.':
            if getattr(self.value, bg_color[1:], Undefined) is not Undefined:
                self.sync_value(bg_color[1:], '_foreground_color', 'from')
        else:
            self._background_color = bg_color  
            
        self._palette = QtGui.QPalette()
        self.control.setAutoFillBackground(True)
        self._palette.setColor(self.control.backgroundRole(), self._background_color)
        self._palette.setColor(self.control.foregroundRole(), self._foreground_color)
        self.control.setPalette(self._palette)      
    
    #---------------------------------------------------------------------------
    #  Updates the editor when the object trait changes external to the editor:
    #---------------------------------------------------------------------------

    def update_editor ( self ):
        """ 
        Updates the editor when the object trait changes externally to the
        editor.
        """
        self.control.setText(self.str_value)
        
    def _foreground_color_changed(self, old, new):
        self._palette.setColor(self.control.foregroundRole(), self._foreground_color)
        self.control.setPalette(self._palette) 
    
    def _background_color_changed(self, old, new):
        self._palette.setColor(self.control.backRole(), self._background_color)
        self.control.setPalette(self._palette) 
        
# editor factory
class ColorTextEditor(BasicEditorFactory):
    """
    Editor factory for a color text editor
    """
    
    klass = _ColorTextEditor
    
    foreground_color = Str
    """The foreground color"""
    
    background_color = Str
    """The background color"""

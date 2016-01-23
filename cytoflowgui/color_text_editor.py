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
Created on Oct 2, 2015

@author: brian
'''

from pyface.qt import QtGui, QtCore
from traitsui.qt4.editor_factory import ReadonlyEditor
from traitsui.api import BasicEditorFactory
from traits.api import Color, Instance, Str, Undefined, Bool

class ColorText(ReadonlyEditor):
    """ Read-only style of text editor, which displays a read-only text field.
    """

    _palette = Instance(QtGui.QPalette)
    _foreground_color = Color
    _background_color = Color

    def init(self, parent):
        """ Finishes initializing the editor by creating the underlying toolkit
            widget.
        """
        
        # I don't seem to be able to just call super() ???
        
        self.control = QtGui.QLabel(self.str_value)

        if self.item.resizable is True or self.item.height != -1.0:
            self.control.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                       QtGui.QSizePolicy.Expanding)
            self.control.setWordWrap(True)

        alignment = None
        for item in self.factory.text_alignment.split(",") :
            item_alignment = self.text_alignment_map.get(item, None)
            if item_alignment :
                if alignment :
                    alignment = alignment | item_alignment
                else :
                    alignment = item_alignment

        if alignment :
            self.control.setAlignment(alignment)

        self.set_tooltip()   
        
        # up to here is copied from traitsui.qt4.editor_factory.ReadonlyEditor     

        flags = (self.control.textInteractionFlags() |
                 QtCore.Qt.TextSelectableByMouse)
        self.control.setTextInteractionFlags(flags)

        if self.factory.word_wrap:
            self.control.setWordWrap(True)

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
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        self.control.setText(self.str_value)
        
    def _foreground_color_changed(self, old, new):
        print "foreground color updated: ", self._foreground_color
        self._palette.setColor(self.control.foregroundRole(), self._foreground_color)
        self.control.setPalette(self._palette) 
    
    def _background_color_changed(self, old, new):
        print "background color updated: ", self._background_color
        self._palette.setColor(self.control.backRole(), self._background_color)
        self.control.setPalette(self._palette) 
        
# editor factory
class ColorTextEditor(BasicEditorFactory):
    klass = ColorText
    foreground_color = Str
    background_color = Str
    word_wrap = Bool

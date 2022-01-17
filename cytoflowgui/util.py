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
cytoflowgui.util
----------------

A few utility classes for `cytoflowgui`
'''

from traits.api import Str
from pyface.ui.qt4.file_dialog import FileDialog

class DefaultFileDialog(FileDialog):
    """A ``pyface.ui.qt4.file_dialog.FileDialog`` with a default suffix"""
    
    default_suffix = Str
    
    def _create_control(self, parent):
        dlg = FileDialog._create_control(self, parent)
        dlg.setDefaultSuffix(self.default_suffix)
        return dlg


from pyface.qt import QtGui

class HintedMainWindow(QtGui.QMainWindow):
    """
    When pyface makes a new dock pane, it sets the width and height as fixed
    (from the new layout or from the default).  Then, after it's finished
    setting up, it resets the minimum and maximum widget sizes.  In Qt5, this
    triggers a re-layout according to the widgets' hinted sizes.  So, here
    we keep track of "fixed" sizes, then return those sizes as the size hint
    to the layout engine.
    """
    
    hint_width = None
    hint_height = None
    
    def setFixedWidth(self, *args, **kwargs):
        self.hint_width = args[0]
        return QtGui.QMainWindow.setFixedWidth(self, *args, **kwargs)
    
    def setFixedHeight(self, *args, **kwargs):
        self.hint_height = args[0]
        return QtGui.QMainWindow.setFixedHeight(self, *args, **kwargs)
    
    def sizeHint(self, *args, **kwargs):
        hint = QtGui.QMainWindow.sizeHint(self, *args, **kwargs)
        if self.hint_width is not None:
            hint.setWidth(self.hint_width)
            
        if self.hint_height is not None:
            hint.setHeight(self.hint_height)
            
        return hint
    
class HintedWidget(QtGui.QWidget):
    """
    When pyface makes a new widget, it sets the width and height as fixed
    (from the new layout or from the default).  Then, after it's finished
    setting up, it resets the minimum and maximum widget sizes.  In Qt5, this
    triggers a re-layout according to the widgets' hinted sizes.  So, here
    we keep track of "fixed" sizes, then return those sizes as the size hint
    to the layout engine.
    """
    
    hint_width = None
    hint_height = None
    
    def setFixedWidth(self, *args, **kwargs):
        self.hint_width = args[0]
        return QtGui.QMainWindow.setFixedWidth(self, *args, **kwargs)
    
    def setFixedHeight(self, *args, **kwargs):
        self.hint_height = args[0]
        return QtGui.QMainWindow.setFixedHeight(self, *args, **kwargs)
    
    def sizeHint(self, *args, **kwargs):
        hint = QtGui.QMainWindow.sizeHint(self, *args, **kwargs)
        if self.hint_width is not None:
            hint.setWidth(self.hint_width)
            
        if self.hint_height is not None:
            hint.setHeight(self.hint_height)
            
        return hint

    
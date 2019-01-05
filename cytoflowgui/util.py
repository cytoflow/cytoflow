#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2019
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
Created on Apr 18, 2015

@author: brian
'''

from traits.api import Unicode
from pyface.ui.qt4.file_dialog import FileDialog

from queue import PriorityQueue

class UniquePriorityQueue(PriorityQueue):
    """
    A PriorityQueue that only allows one copy of each item.
    http://stackoverflow.com/questions/5997189/how-can-i-make-a-unique-value-priority-queue-in-python
    """
    
    def _init(self, maxsize):
        PriorityQueue._init(self, maxsize)
        self.values = set()

    def _put(self, item):
        if item[1] not in self.values:
            self.values.add(item[1])
            PriorityQueue._put(self, item)
        else:
            pass

    def _get(self):
        item = PriorityQueue._get(self)
        self.values.remove(item[1])
        return item
    
def filter_unpicklable(obj):
    if type(obj) is list:
        return [filter_unpicklable(x) for x in obj]
    elif type(obj) is dict:
        return {x: filter_unpicklable(obj[x]) for x in obj}
    else:
        if not hasattr(obj, '__getstate__') and not isinstance(obj,
                  (str, int, float, tuple, list, set, dict)):
            return "filtered: {}".format(type(obj))
        else:
            return obj
        
class DefaultFileDialog(FileDialog):
    default_suffix = Unicode
    
    def _create_control(self, parent):
        dlg = FileDialog._create_control(self, parent)
        dlg.setDefaultSuffix(self.default_suffix)
        return dlg

class IterWrapper(object):
    def __init__(self, iterator, by):
        self.iterator = iterator
        self.by = by
        
    def __iter__(self):
        return self
        
    def __next__(self):
        return next(self.iterator)
    
# when pyface makes a new dock pane, it sets the width and height as fixed
# (from the new layout or from the default).  then, after it's finished
# setting up, it resets the minimum and maximum widget sizes.  in Qt5, this
# triggers a re-layout according to the widgets' hinted sizes.  so, here
# we keep track of "fixed" sizes, then return those sizes as the size hint
# to the layout engine.

from pyface.qt import QtGui

class HintedMainWindow(QtGui.QMainWindow):
    
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


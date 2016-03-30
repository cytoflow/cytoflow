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

"""
Render to qt from agg
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import ctypes

from matplotlib.figure import Figure

from matplotlib.backends.backend_qt4 import QtCore

##### not used in this module, but needed for pylab_setup
from matplotlib.backends.backend_qt4 import show  # @UnusedImport
from matplotlib.backends.backend_qt4 import draw_if_interactive as qt4_draw_if_interactive
from matplotlib.backends.backend_qt4 import backend_version  # @UnusedImport
######

from matplotlib.backend_bases import FigureManagerBase

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg

DEBUG = False

_decref = ctypes.pythonapi.Py_DecRef
_decref.argtypes = [ctypes.py_object]
_decref.restype = None

class FigureManagerCytoflow(FigureManagerBase):
    """
    Public attributes

    canvas      : The FigureCanvas instance
    num         : The Figure number
    toolbar     : The qt.QToolBar
    window      : The qt.QMainWindow
    """

    def __init__(self, canvas, num):
        print ("new figure manager")
        FigureManagerBase.__init__(self, canvas, num)
        self.canvas = canvas

        # Give the keyboard focus to the figure instead of the
        # manager; StrongFocus accepts both tab and click to focus and
        # will enable the canvas to process event w/o clicking.
        # ClickFocus only takes the focus if the window has been
        # clicked on. 
        # http://qt-project.org/doc/qt-4.8/qt.html#FocusPolicy-enum or
        # http://doc.qt.digia.com/qt/qt.html#FocusPolicy-enum
        self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.canvas.setFocus()
        
    def show(self):
        print("show figure")
        pass
    
    def destroy(self):
        print ("destroy figure")
        pass
    
    def resize(self):
        print ("resize figure")
        
def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    
    # TODO - register the new figure/canvas with the editor?  the task?
    # anyways, something; then, seaborn can plot at will and render to
    # the aggregator associated with this canvas; and when it's done,
    # we can swap in the canvas in the ui.
    
    # this also will solve the multithreading plotting problem, because
    # only the swap/draw_if_interactive has to happen on the UI thread;
    # the rest of the rendering to the agg can happen in another thread.
    
    FigureClass = kwargs.pop('FigureClass', Figure)
    thisFig = FigureClass(*args, **kwargs)

    # the default figure size in Seaborn is 3 inches x 3 inches.  the framework
    # should stretch this out .... but it doesn't.  i don't know why.  so,
    # we set the dpi and figure size manually here ..... why?  i don't know.
    thisFig.set_dpi(96)
    thisFig.set_size_inches(5, 5)
    canvas = FigureCanvasQTAgg(thisFig)
    return FigureManagerCytoflow(canvas, num)

def draw_if_interactive():
    print ("draw if interactive")

    qt4_draw_if_interactive()


FigureCanvas = FigureCanvasQTAgg
FigureManager = FigureManagerCytoflow


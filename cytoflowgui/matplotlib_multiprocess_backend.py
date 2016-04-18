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

import multiprocessing

from matplotlib.figure import Figure

from matplotlib.backends.backend_qt4 import QtCore, FigureCanvasQT
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAggBase
from matplotlib.backends.backend_agg import FigureCanvasAgg

# needed for pylab_setup
backend_version = "0.1.0"

from matplotlib.backend_bases import FigureManagerBase

DEBUG = False

_decref = ctypes.pythonapi.Py_DecRef
_decref.argtypes = [ctypes.py_object]
_decref.restype = None

# multiprocess plotting:  the process boundary is at the canvas.  two canvases
# will be needed, a local canvas and a remote canvas.  the remote canvas will
# be the destination of the Agg renderer; when its draw() is called, it will
# push the image buffer to the UI process, which will draw it on the screen.
# the local canvas will handle all UI events, and push them to the remote
# canvas to process (if registered.)

local_mpl_conn, remote_mpl_conn = multiprocessing.Pipe()

class FigureCanvasQTAggLocal(FigureCanvasQTAggBase,
                             FigureCanvasQT,
                             FigureCanvasAgg):
    """
    The canvas the figure renders into.  Calls the draw and print fig
    methods, creates the renderers, etc...
    Public attribute
      figure - A Figure instance
   """

    def __init__(self, figure):
        print("Init local canvas")
        if DEBUG:
            print('FigureCanvasQtAgg: ', figure)
        FigureCanvasQT.__init__(self, figure)
        FigureCanvasQTAggBase.__init__(self, figure)
        FigureCanvasAgg.__init__(self, figure)
        self._drawRect = None
        self.blitbox = None
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)    

class FigureCanvasAggRemote(FigureCanvasAgg):
    """
    The canvas the figure renders into.  Calls the draw and print fig
    methods, creates the renderers, etc...
    Public attribute
      figure - A Figure instance
   """

    def __init__(self, figure):
        if DEBUG:
            print('FigureCanvasAggRemote: ', figure)
        FigureCanvasAgg.__init__(self, figure)
        self.blitbox = None
        
    def draw(self):
        print("Remote draw")
        FigureCanvasAgg.draw(self)
        # TODO - send buffer to local process    

class FigureManagerCytoflowRemote(FigureManagerBase):
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
        # self.canvas.setFocusPolicy(QtCore.Qt.StrongFocus)
        #self.canvas.setFocus()
        
    def show(self):
        print("show figure")
    
    def destroy(self):
        print ("destroy figure")
    
    def resize(self):
        print ("resize figure")
        
def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    
    print("new figure manager")
    
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
    canvas = FigureCanvasAggRemote(thisFig)
    return FigureManagerCytoflowRemote(canvas, num)

def draw_if_interactive():
    print ("draw if interactive")
    
def show():
    print ("show")

FigureCanvas = FigureCanvasAggRemote
FigureManager = FigureManagerCytoflowRemote
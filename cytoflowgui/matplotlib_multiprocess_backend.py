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

import sys, time, threading

import matplotlib.pyplot
from matplotlib.figure import Figure

from matplotlib.backends.backend_qt4 import FigureCanvasQT
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAggBase
from matplotlib.backends.backend_agg import FigureCanvasAgg

from pyface.qt import QtCore, QtGui

# needed for pylab_setup
backend_version = "0.0.1"

from matplotlib.backend_bases import FigureManagerBase

# multiprocess plotting:  the process boundary is at the canvas.  two canvases
# will be needed, a local canvas and a remote canvas.  the remote canvas will
# be the destination of the Agg renderer; when its draw() is called, it will
# push the image buffer to the UI process, which will draw it on the screen.
# the local canvas will handle all UI events, and push them to the remote
# canvas to process (if registered.)

# pipe connections for communicating between canvases
# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.parent_conn = None
this.child_conn = None
this.remote_canvas = None

DEBUG = 1

class Msg:
    DRAW = 0
    DONE_DRAWING = 1
    RESIZE_FIGURE = 2

class FigureCanvasQTAggLocal(FigureCanvasQTAggBase,
                             FigureCanvasQT,
                             FigureCanvasAgg):
    """
    The local canvas; ie, the one in the GUI.
      figure - A Figure instance
   """

    def __init__(self, figure):
        print("Init local canvas")

        FigureCanvasQT.__init__(self, figure)
        FigureCanvasQTAggBase.__init__(self, figure)
        FigureCanvasAgg.__init__(self, figure)
        self._drawRect = None
        self.blitbox = None
        self.buffer = None

        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)    
        
        threading.Thread(target = self.listen_for_remote, args = ()).start()
        
    def listen_for_remote(self):
        while this.child_conn is None:
            time.sleep(0.5)

        while True:
            msg = this.child_conn.recv()
            if DEBUG:
                print("FigureCanvasQTAggLocal.listen_for_remote :: {}".format(msg))
            if msg == Msg.DRAW:
                self.buffer = this.child_conn.recv()
                self.buffer_width = this.child_conn.recv()
                self.buffer_height = this.child_conn.recv()
                self.update()
            else:
                raise RuntimeError("FigureCanvasQTAggLocal received bad message {}".format(msg))
            
    def send_to_remote(self):
        pass
        
    def draw(self):
        if DEBUG:
            print("FigureCanvasQTAggLocal.draw()")
        self.update()
        # print("Local draw")
        # FigureCanvasAgg.draw(self)
        # TODO - send buffer to local process  
        
    def paintEvent(self, e):
        """
        Copy the image from the buffer to the qt.drawable.
        In Qt, all drawing should be done inside of here when a widget is
        shown onscreen.
        """
        
        if self.buffer is None:
            return

        if DEBUG:
            print('FigureCanvasQtAggLocal.paintEvent: ', self,
                  self.get_width_height())

        if self.blitbox is None:
            
            # convert the Agg rendered image -> qImage
            qImage = QtGui.QImage(self.buffer, self.buffer_width,
                                  self.buffer_height,
                                  QtGui.QImage.Format_ARGB32)
            # get the rectangle for the image
            rect = qImage.rect()
            p = QtGui.QPainter(self)
            # reset the image area of the canvas to be the back-ground color
            p.eraseRect(rect)
            # draw the rendered image on to the canvas
            p.drawPixmap(QtCore.QPoint(0, 0), QtGui.QPixmap.fromImage(qImage))

            # draw the zoom rectangle to the QPainter
            if self._drawRect is not None:
                p.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DotLine))
                x, y, w, h = self._drawRect
                p.drawRect(x, y, w, h)
            p.end()
            
            # self.buffer = None

        else:
            pass
#             bbox = self.blitbox
#             l, b, r, t = bbox.extents
#             w = int(r) - int(l)
#             h = int(t) - int(b)
#             t = int(b) + h
#             reg = self.copy_from_bbox(bbox)
#             stringBuffer = reg.to_string_argb()
#             qImage = QtGui.QImage(stringBuffer, w, h,
#                                   QtGui.QImage.Format_ARGB32)
# 
#             pixmap = QtGui.QPixmap.fromImage(qImage)
#             p = QtGui.QPainter(self)
#             p.drawPixmap(QtCore.QPoint(l, self.renderer.height-t), pixmap)
# 
#             # draw the zoom rectangle to the QPainter
#             if self._drawRect is not None:
#                 p.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DotLine))
#                 x, y, w, h = self._drawRect
#                 p.drawRect(x, y, w, h)
#             p.end()
#             self.blitbox = None  

    def resizeEvent(self, event):
        w = event.size().width()
        h = event.size().height()
        if DEBUG:
            print("FigureCanvasQTAggLocal.resizeEvent(%d, %d)" % (w, h))
        dpival = self.figure.dpi
        winch = w / dpival
        hinch = h / dpival
        
        this.child_conn.send(Msg.RESIZE_FIGURE)
        this.child_conn.send(winch)
        this.child_conn.send(hinch)
        
        #self.figure.set_size_inches(winch, hinch)
        FigureCanvasAgg.resize_event(self)
        #self.draw_idle()
        #QtWidgets.QWidget.resizeEvent(self, event)

class FigureCanvasAggRemote(FigureCanvasAgg):
    """
    The canvas the figure renders into in the remote process (ie, the one
    where someone is calling pyplot.plot()
   """

    def __init__(self, figure):
        FigureCanvasAgg.__init__(self, figure)
        self.blitbox = None
        
        self.update = threading.Event()
        
        threading.Thread(target = self.listen_for_remote, args = ()).start()
        threading.Thread(target = self.send_to_remote, args=()).start()
        
    def listen_for_remote(self): 
        while True:
            msg = this.parent_conn.recv()
            if DEBUG:
                print("FigureCanvasAggRemote.listen_for_remote :: {}".format(msg))
            if msg == Msg.RESIZE_FIGURE:
                winch = this.parent_conn.recv()
                hinch = this.parent_conn.recv()
                self.figure.set_size_inches(winch, hinch)
                self.update.set()
            else:
                raise RuntimeError("FigureCanvasAggRemote received bad message {}".format(msg))
            
    def send_to_remote(self):
        while self.update.wait():
            self.update.clear()
            
            FigureCanvasAgg.draw(self)
                
            if QtCore.QSysInfo.ByteOrder == QtCore.QSysInfo.LittleEndian:
                str_buffer = self.renderer._renderer.tostring_bgra()
            else:
                str_buffer = self.renderer._renderer.tostring_argb()    
                
            this.parent_conn.send(Msg.DRAW)
            this.parent_conn.send(str_buffer)
            this.parent_conn.send(self.renderer.width)
            this.parent_conn.send(self.renderer.height)
        
    def draw(self):
        if DEBUG:
            print("FigureCanvasAggRemote.draw()")

        self.update.set()
        
    def blit(self, bbox = None):
        print("Tried to blit .... not yet implemented")
        pass
    

def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """

    # make a new figure
    FigureClass = kwargs.pop('FigureClass', Figure)
    newFig = FigureClass(*args, **kwargs)
 
    # the canvas is a singleton.
    if not this.remote_canvas:
        this.remote_canvas = FigureCanvasAggRemote(newFig)
    else:        
        oldFig = this.remote_canvas.figure
        newFig.set_size_inches(oldFig.get_figwidth(), oldFig.get_figheight())
        this.remote_canvas.figure = newFig
        
    newFig.set_canvas(this.remote_canvas)

    # close the current figure (to keep pyplot happy)
    matplotlib.pyplot.close()
 
    return FigureManagerBase(this.remote_canvas, num)

def draw_if_interactive():
    this.remote_canvas.draw()

# make sure pyplot uses the remote canvas
FigureCanvas = FigureCanvasAggRemote

# we don't need a figure manager with any more than default functionality
FigureManager = FigureManagerBase
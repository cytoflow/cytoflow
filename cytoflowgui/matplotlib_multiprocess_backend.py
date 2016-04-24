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

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
#from matplotlib.backends.backend_qt5agg import FigureCanvasQTAggBase
from matplotlib.backends.backend_agg import FigureCanvasAgg

from pyface.qt import QtCore, QtGui

# needed for pylab_setup
backend_version = "0.0.1"

# matplotlib.interactive(True)

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
    BLIT = 1
    
    RESIZE_EVENT = 2
    MOUSE_PRESS_EVENT = 3
    MOUSE_MOVE_EVENT = 4
    MOUSE_RELEASE_EVENT = 5

class FigureCanvasQTAggLocal(FigureCanvasQTAgg):
    """
    The local canvas; ie, the one in the GUI.
      figure - A Figure instance
   """

    def __init__(self, figure):
        print("Init local canvas")

        FigureCanvasQTAgg.__init__(self, figure)
        self._drawRect = None
        self.blitbox = None
        
        # self.buffer_lock = threading.Lock
        self.buffer = None
        self.buffer_width = None
        self.buffer_height = None
        
        # self.blit_lock = threading.Lock
        self.blit_buffer = None
        self.blit_width = None
        self.blit_height = None
        self.blit_top = None
        self.blit_left = None

        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)    
        
        threading.Thread(target = self.listen_for_remote, args = ()).start()
        
    def listen_for_remote(self):
        while this.child_conn is None:
            time.sleep(0.5)

        while True:
            (msg, payload) = this.child_conn.recv()
            if DEBUG:
                print("FigureCanvasQTAggLocal.listen_for_remote :: {}".format(msg))
            if msg == Msg.DRAW:
                self.buffer, self.buffer_width, self.buffer_height = payload 
                self.update()
            elif msg == Msg.BLIT:
                self.blit_buffer, self.blit_width, self.blit_height, \
                    self.blit_top, self.blit_left = payload
                self.update()
            else:
                raise RuntimeError("FigureCanvasQTAggLocal received bad message {}".format(msg))
            
    def send_to_remote(self):
        pass
    
#     def enterEvent(self, event):
#         FigureCanvasQTAgg.enter_notify_event(self, guiEvent=event)

#     def leaveEvent(self, event):
#         QtWidgets.QApplication.restoreOverrideCursor()
#         FigureCanvasQT.leave_notify_event(self, guiEvent=event)

    def mousePressEvent(self, event):
        x = event.pos().x()
        # flip y so y=0 is bottom of canvas
        y = self.figure.bbox.height - event.pos().y()
        button = self.buttond.get(event.button())
        if button is not None:
            msg = (Msg.MOUSE_PRESS_EVENT, (x, y, button))
            this.child_conn.send(msg)
        if DEBUG:
            print('button pressed:', event.button())

    def mouseDoubleClickEvent(self, event):
        pass
#         x = event.pos().x()
#         # flipy so y=0 is bottom of canvas
#         y = self.figure.bbox.height - event.pos().y()
#         button = self.buttond.get(event.button())
#         if button is not None:
#             FigureCanvasQT.button_press_event(self, x, y,
#                                               button, dblclick=True,
#                                               guiEvent=event)
#         if DEBUG:
#             print('button doubleclicked:', event.button())

    def mouseMoveEvent(self, event):
        x = event.x()
        # flipy so y=0 is bottom of canvas
        y = self.figure.bbox.height - event.y()
        msg = (Msg.MOUSE_MOVE_EVENT, (x, y))
        this.child_conn.send(msg)
#        FigureCanvasQT.motion_notify_event(self, x, y, guiEvent=event)
        if DEBUG: 
            print('mouse move')

    def mouseReleaseEvent(self, event):
        x = event.x()
        # flip y so y=0 is bottom of canvas
        y = self.figure.bbox.height - event.y()
        button = self.buttond.get(event.button())
        if button is not None:
#             FigureCanvasQT.button_release_event(self, x, y, button,
#                                                   guiEvent=event)
            msg = (Msg.MOUSE_RELEASE_EVENT, (x, y, button))
            this.child_conn.send(msg)
        if DEBUG:
            print('button released')

#     def draw(self):
#         if DEBUG:
#             print("FigureCanvasQTAggLocal.draw()")
#         self.update()


        
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

        if self.blit_buffer is None:
            
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
                print("drawRect not yet implemented (local)")
#                 p.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DotLine))
#                 x, y, w, h = self._drawRect
#                 p.drawRect(x, y, w, h)
            p.end()
            
            # self.buffer = None

        else:
            qImage = QtGui.QImage(self.blit_buffer, 
                                  self.blit_width,
                                  self.blit_height,
                                  QtGui.QImage.Format_ARGB32)
 
            pixmap = QtGui.QPixmap.fromImage(qImage)
            p = QtGui.QPainter(self)
            p.drawPixmap(QtCore.QPoint(self.blit_left, 
                                       self.buffer_height - self.blit_top), 
                         pixmap)
 
            # draw the zoom rectangle to the QPainter
            if self._drawRect is not None:
                print("drawRect isn't implemented yet")
#                 p.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.DotLine))
#                 x, y, w, h = self._drawRect
#                 p.drawRect(x, y, w, h)
            p.end()
            self.blit_buffer = None

    def resizeEvent(self, event):
        w = event.size().width()
        h = event.size().height()
        if DEBUG:
            print("FigureCanvasQTAggLocal.resizeEvent(%d, %d)" % (w, h))
        dpival = self.figure.dpi
        winch = w / dpival
        hinch = h / dpival
        
        msg = (Msg.RESIZE_EVENT, (winch, hinch))
        this.child_conn.send(msg)
        
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
        
        self.buffer_lock = threading.Lock()
        self.buffer = None
        self.buffer_width = None
        self.buffer_height = None
        
        self.blit_lock = threading.Lock()
        self.blit_buffer = None
        self.blit_width = None
        self.blit_height = None
        self.blit_top = None
        self.blit_left = None
        
        self.update_remote = threading.Event()
        
        threading.Thread(target = self.listen_for_remote, args = ()).start()
        threading.Thread(target = self.send_to_remote, args=()).start()
        
    def listen_for_remote(self): 
        while True:
            (msg, payload) = this.parent_conn.recv()
            if DEBUG:
                print("FigureCanvasAggRemote.listen_for_remote :: {}".format(msg))
            if msg == Msg.RESIZE_EVENT:
                winch, hinch = payload
                self.figure.set_size_inches(winch, hinch)
                self.draw()
            elif msg == Msg.MOUSE_PRESS_EVENT:
                x, y, button = payload
                FigureCanvasAgg.button_press_event(self, x, y, button)
            elif msg == Msg.MOUSE_RELEASE_EVENT:
                x, y, button = payload
                FigureCanvasAgg.button_release_event(self, x, y, button)
            elif msg == Msg.MOUSE_MOVE_EVENT:
                x, y = payload
                FigureCanvasAgg.motion_notify_event(self, x, y)
            else:
                raise RuntimeError("FigureCanvasAggRemote received bad message {}".format(msg))
            
    def send_to_remote(self):
        while self.update_remote.wait():
            if DEBUG:
                print("FigureCanvasAggRemote.send_to_remote")
                
            self.update_remote.clear()
            
            if self.blit_buffer is None:
                with self.buffer_lock:
                    msg = (Msg.DRAW, (self.buffer,
                                      self.buffer_width, 
                                      self.buffer_height))
                    this.parent_conn.send(msg)
            else:
                with self.blit_lock:
                    msg = (Msg.BLIT, (self.blit_buffer,
                                      self.blit_width,
                                      self.blit_height,
                                      self.blit_top,
                                      self.blit_left))
                    this.parent_conn.send(msg)
                    self.blit_buffer = None
        
    def draw(self, *args, **kwargs):
        if DEBUG:
            print("FigureCanvasAggRemote.draw()")
            
        with self.buffer_lock:
            FigureCanvasAgg.draw(self)
                
            if QtCore.QSysInfo.ByteOrder == QtCore.QSysInfo.LittleEndian:
                self.buffer = self.renderer._renderer.tostring_bgra()
            else:
                self.buffer = self.renderer._renderer.tostring_argb()    
                
            self.buffer_width = self.renderer.width
            self.buffer_height = self.renderer.height

            self.update_remote.set()
    
#     def mpl_connect(self, s, func):
#         if DEBUG:
#             print("FigureCanvasAggRemote.mpl_connect()")
        

    def blit(self, bbox=None):
        """
        Blit the region in bbox
        """
        # If bbox is None, blit the entire canvas. Otherwise
        # blit only the area defined by the bbox.
        if bbox is None and self.figure:
            bbox = self.figure.bbox

        l, b, r, t = bbox.extents
        w = int(r) - int(l)
        h = int(t) - int(b)
        t = int(b) + h
        l = int(l)
        reg = self.copy_from_bbox(bbox)
        
        with self.blit_lock:
            self.blit_buffer = reg.to_string_argb()
            self.blit_width = w
            self.blit_height = h
            self.blit_top = t
            self.blit_left = l
            
        self.update_remote.set()
#         l, b, w, h = bbox.bounds
#         t = b + h
#         self.repaint(l, self.renderer.height-t, w, h)
    

def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance
    """
    
    if DEBUG:
        print("mpl_multiprocess_backend.new_figure_manager()")

    # make a new figure
    FigureClass = kwargs.pop('FigureClass', Figure)
    new_fig = FigureClass(*args, **kwargs)
 
    # the canvas is a singleton.
    if not this.remote_canvas:
        this.remote_canvas = FigureCanvasAggRemote(new_fig)
    else:        
        # TODO - this doesn't update the canvas patch, so we
        # don't get mouse events.  
        old_fig = this.remote_canvas.figure
        new_fig.set_size_inches(old_fig.get_figwidth(), 
                                old_fig.get_figheight())
        this.remote_canvas.figure = new_fig
        
    new_fig.set_canvas(this.remote_canvas)

    # close the current figure (to keep pyplot happy)
    matplotlib.pyplot.close()
 
    return FigureManagerBase(this.remote_canvas, num)


def draw_if_interactive():
    if DEBUG:
        print ("mpl_multiprocess_backend.draw_if_interactive")
    this.remote_canvas.draw()
    
def show():
    if DEBUG:
        print ("mpl_multiprocess_backend.show")
    this.remote_canvas.draw()

# make sure pyplot uses the remote canvas
FigureCanvas = FigureCanvasAggRemote

# we don't need a figure manager with any more than default functionality
FigureManager = FigureManagerBase
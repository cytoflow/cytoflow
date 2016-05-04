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
A matplotlib backend that renders across a process boundary.

By default, matplotlib only works in one thread.  For a GUI application, this
is a problem because when matplotlib is working (ie, scaling a bunch of data
points) the GUI freezes.

This module implements a matplotlib backend where the plotting done in one
process (ie via pyplot, etc) shows up in a canvas running in another process
(the GUI).  The canvas is the interface across the process boundary: a "local"
canvas, which is a GUI widget (in this case a QWidget) and a "remote" canvas
(running in the process where pyplot.plot() etc. are used.)  The remote canvas
is a subclass of the Agg renderer; when draw() is called, the remote canvas
pulls the current buffer out of the renderer and pushes it through a pipe
to the local canvas, which draws it on the screen.  blit() is implemented
too.

This takes care of one direction of data flow, and would be enough if we were
just plotting.  However, we want to use matplotlib widgets as well, which
means there's data flowing from the local canvas to the remote canvas too.
The local canvas is a subclass of FigureCanvasQTAgg, which is itself a 
sublcass of QWidget.  The local canvas overrides several of the event handlers,
passing the event information to the remote canvas which in turn runs the
matplotlib event handlers.
"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import sys, time, threading

import matplotlib.pyplot
from matplotlib.figure import Figure

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg

from pyface.qt import QtCore, QtGui

# needed for pylab_setup
backend_version = "0.0.2"

from matplotlib.backend_bases import FigureManagerBase


# module-level pipe connections for communicating between canvases.
# these are initialized in cytoflow_application, which starts the remote
# process.

# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.parent_conn = None
this.child_conn = None
this.remote_canvas = None

DEBUG = 0

class Msg:
    DRAW = "DRAW"
    BLIT = "BLIT"
    
    RESIZE_EVENT = "RESIZE"
    MOUSE_PRESS_EVENT = "MOUSE_PRESS"
    MOUSE_MOVE_EVENT = "MOUSE_MOVE"
    MOUSE_RELEASE_EVENT = "MOUSE_RELEASE"
    MOUSE_DOUBLE_CLICK_EVENT = "MOUSE_DOUBLE_CLICK"
    
    PRINT = "PRINT"

class FigureCanvasQTAggLocal(FigureCanvasQTAgg):
    """
    The local canvas; ie, the one in the GUI.
      figure - A Figure instance
   """

    def __init__(self, figure):
        FigureCanvasQTAgg.__init__(self, figure)
        self._drawRect = None
        self.blitbox = None
        
        self.buffer = None
        self.buffer_width = None
        self.buffer_height = None
        
        self.blit_buffer = None
        self.blit_width = None
        self.blit_height = None
        self.blit_top = None
        self.blit_left = None

        # positions to send
        self.move_x = None
        self.move_y = None
        self.resize_width = None
        self.resize_height = None
        self.send_event = threading.Event()
        
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)    
        
        t = threading.Thread(target = self.listen_for_remote, 
                             name = "canvas listen",
                             args = ())
        t.daemon = True
        t.start()
        
        t = threading.Thread(target = self.send_to_remote, 
                             name = "canvas send",
                             args = ())
        t.daemon = True
        t.start()
        
    def listen_for_remote(self):
        while this.child_conn.poll():
            try:
                (msg, payload) = this.child_conn.recv()
            except EOFError:
                return
            
            if DEBUG:
                print("FigureCanvasQTAggLocal.listen_for_remote :: {}".format(msg))
            
            if msg == Msg.DRAW:
                (self.buffer, 
                 self.buffer_width, 
                 self.buffer_height) = payload 
                self.update()
            elif msg == Msg.BLIT:
                (self.blit_buffer, 
                 self.blit_width, 
                 self.blit_height,
                 self.blit_top, 
                 self.blit_left) = payload
                self.update()
            else:
                raise RuntimeError("FigureCanvasQTAggLocal received bad message {}".format(msg))
            
            
    def send_to_remote(self):
        while True:
            self.send_event.wait()
            self.send_event.clear()
            
            if self.move_x:
                if DEBUG:
                    print('FigureCanvasQTAggLocal.send_to_remote: {}', (Msg.MOUSE_MOVE_EVENT, self.move_x, self.move_y))
                msg = (Msg.MOUSE_MOVE_EVENT, (self.move_x, self.move_y))
                this.child_conn.send(msg)
                self.move_x = self.move_y = None
                
            if self.resize_width:
                if DEBUG:
                    print('FigureCanvasQTAggLocal.send_to_remote: {}', (Msg.RESIZE_EVENT, self.resize_width, self.resize_height))
                msg = (Msg.RESIZE_EVENT, (self.resize_width, self.resize_height))
                this.child_conn.send(msg)
                self.resize_width = self.resize_height = None

            # for performance reasons, make sure there are no more than
            # 10 updates per second
            time.sleep(0.1)
            

    def leaveEvent(self, event):
        QtGui.QApplication.restoreOverrideCursor()


    def mousePressEvent(self, event):
        if DEBUG:
            print('FigureCanvasQTAggLocal.mousePressEvent: {}', event.button())
        x = event.pos().x()
        # flip y so y=0 is bottom of canvas
        y = self.figure.bbox.height - event.pos().y()
        button = self.buttond.get(event.button())
        if button is not None:
            msg = (Msg.MOUSE_PRESS_EVENT, (x, y, button))
            this.child_conn.send(msg)
            
            
    def mouseDoubleClickEvent(self, event):
        if DEBUG:
            print('FigureCanvasQTAggLocal.mouseDoubleClickEvent: {}', event.button())
        x = event.pos().x()
        # flipy so y=0 is bottom of canvas
        y = self.figure.bbox.height - event.pos().y()
        button = self.buttond.get(event.button())
        if button is not None:
            msg = (Msg.MOUSE_DOUBLE_CLICK_EVENT, (x, y, button))
            this.child_conn.send(msg)


    def mouseMoveEvent(self, event):
#         if DEBUG:
#             print('FigureCanvasQTAggLocal.mouseMoveEvent: {}', (event.x(), event.y()))
        self.move_x = event.x()
        # flip y so y=0 is bottom of canvas
        self.move_y = int(self.figure.bbox.height) - event.y()
        self.send_event.set()


    def mouseReleaseEvent(self, event):
        if DEBUG:
            print('FigureCanvasQTAggLocal.mouseReleaseEvent: {}', event.button())
        x = event.x()
        # flip y so y=0 is bottom of canvas
        y = self.figure.bbox.height - event.y()
        button = self.buttond.get(event.button())
        if button is not None:
            msg = (Msg.MOUSE_RELEASE_EVENT, (x, y, button))
            this.child_conn.send(msg)


    def resizeEvent(self, event):
        w = event.size().width()
        h = event.size().height()
        if DEBUG:
            print("FigureCanvasQTAggLocal.resizeEvent(%d, %d)" % (w, h))
        dpival = self.figure.dpi
        winch = w / dpival
        hinch = h / dpival
        
        self.resize_width = winch
        self.resize_height = hinch

        self.send_event.set()
        
        self.figure.set_size_inches(winch, hinch)
        FigureCanvasAgg.resize_event(self)
        QtGui.QWidget.resizeEvent(self, event)

        
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

            p.end()
            
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
            p.end()
            self.blit_buffer = None
            
    def print_figure(self, *args, **kwargs):
        this.child_conn.send((Msg.PRINT, (args, kwargs)))


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
                
        t = threading.Thread(target = self.listen_for_remote, 
                             name = "canvas listen", 
                             args = ())
        t.daemon = True 
        t.start()
        
        t = threading.Thread(target = self.send_to_remote, 
                             name = "canvas send",
                             args=())
        t.daemon = True
        t.start()
        
    def listen_for_remote(self): 
        while this.parent_conn.poll():
            try:
                (msg, payload) = this.parent_conn.recv()
            except EOFError:
                return
            
            if DEBUG:
                print("FigureCanvasAggRemote.listen_for_remote :: {}".format(msg))
                            
            if msg == Msg.RESIZE_EVENT:
                (winch, hinch) = payload
                self.figure.set_size_inches(winch, hinch)
                FigureCanvasAgg.resize_event(self)
                self.draw()
            elif msg == Msg.MOUSE_PRESS_EVENT:
                (x, y, button) = payload
                FigureCanvasAgg.button_press_event(self, x, y, button)
            elif msg == Msg.MOUSE_DOUBLE_CLICK_EVENT:
                (x, y, button) = payload
                FigureCanvasAgg.button_press_event(self, x, y, button, dblclick = True)
            elif msg == Msg.MOUSE_RELEASE_EVENT:
                (x, y, button) = payload
                FigureCanvasAgg.button_release_event(self, x, y, button)
            elif msg == Msg.MOUSE_MOVE_EVENT:
                (x, y) = payload
                FigureCanvasAgg.motion_notify_event(self, x, y)
            elif msg == Msg.PRINT:
                (args, kwargs) = payload
                FigureCanvasAgg.print_figure(self, *args, **kwargs)
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
        

    def blit(self, bbox=None):
        """
        Blit the region in bbox
        """
        # If bbox is None, blit the entire canvas. Otherwise
        # blit only the area defined by the bbox.
        if DEBUG:
            print("FigureCanvasAggRemote.blit()")
        
        if bbox is None and self.figure:
            print("bbox was none")
            return

        with self.blit_lock:
            l, b, r, t = bbox.extents
            w = int(r) - int(l)
            h = int(t) - int(b)
            t = int(b) + h
            l = int(l)
        
            reg = self.copy_from_bbox(bbox)
            
            self.blit_buffer = reg.to_string_argb()
            self.blit_width = w
            self.blit_height = h
            self.blit_top = t
            self.blit_left = l
            
        self.update_remote.set()
    

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
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
A matplotlib backend that renders across a process boundary.  This file
has the "local" canvas -- the part that actually renders to a (Qt) window.

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

import time, threading, logging, sys, traceback

import matplotlib

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg

from pyface.qt import QtCore, QtGui

logger = logging.getLogger(__name__)

DEBUG = 0

class Msg(object):
    DRAW = "DRAW"
    BLIT = "BLIT"
    WORKING = "WORKING"
    
    RESIZE_EVENT = "RESIZE"
    MOUSE_PRESS_EVENT = "MOUSE_PRESS"
    MOUSE_MOVE_EVENT = "MOUSE_MOVE"
    MOUSE_RELEASE_EVENT = "MOUSE_RELEASE"
    MOUSE_DOUBLE_CLICK_EVENT = "MOUSE_DOUBLE_CLICK"
    
    DPI = "DPI"
    PRINT = "PRINT"
    
def log_exception():
    (exc_type, exc_value, tb) = sys.exc_info()

    err_string = traceback.format_exception_only(exc_type, exc_value)[0]
    err_loc = traceback.format_tb(tb)[-1]
    err_ctx = threading.current_thread().name
    
    logger.debug("Exception in {0}:\n{1}"
                  .format(err_ctx, "".join( traceback.format_exception(exc_type, exc_value, tb) )))
    
    
    logger.error("Error: {0}\nLocation: {1}Thread: {2}" \
                  .format(err_string, err_loc, err_ctx) )
    

class FigureCanvasQTAggLocal(FigureCanvasQTAgg):
    """
    The local canvas; ie, the one in the GUI.
      figure - A Figure instance
   """

    def __init__(self, figure, child_conn, working_pixmap):
        FigureCanvasQTAgg.__init__(self, figure)
        self._drawRect = None
        self.child_conn = child_conn
        
        # set up the "working" pixmap
        self.working = False
        self.working_pixmap = QtGui.QLabel(self)
        self.working_pixmap.setVisible(False)
        self.working_pixmap.setPixmap(working_pixmap)
        self.working_pixmap.setScaledContents(True)
        wp_size = min([self.width(), self.height()]) / 5
        self.working_pixmap.resize(wp_size, wp_size)
        self.working_pixmap.move(self.width() - wp_size,
                                 self.height() - wp_size)
        
        
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
        self._resize_timer = None
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
        
        dpi = self.physicalDpiX()
        figure.dpi = dpi
        matplotlib.rcParams['figure.dpi'] = dpi
        self.child_conn.send((Msg.DPI, self.physicalDpiX()))
        
    def listen_for_remote(self):
        while self.child_conn.poll(None):
            try:
                (msg, payload) = self.child_conn.recv()
            except EOFError:
                return
            
            logger.debug("FigureCanvasQTAggLocal.listen_for_remote :: {}".format(msg))
            
            try:
                if msg == Msg.WORKING:
                    self.working = payload
                    self.working_pixmap.setVisible(self.working)
                elif msg == Msg.DRAW:
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
            except Exception:
                log_exception()
            
            
    def send_to_remote(self):
        while True:
            self.send_event.wait()
            self.send_event.clear()
            
            if self.move_x is not None:
                msg = (Msg.MOUSE_MOVE_EVENT, (self.move_x, self.move_y))
                self.child_conn.send(msg)
                self.move_x = self.move_y = None
                
            if self.resize_width is not None:
                logger.debug('FigureCanvasQTAggLocal.send_to_remote: {}'
                              .format((Msg.RESIZE_EVENT, self.resize_width, self.resize_height)))
                msg = (Msg.RESIZE_EVENT, (self.resize_width, self.resize_height))
                self.child_conn.send(msg)
                self.resize_width = self.resize_height = None

            # for performance reasons, make sure there are no more than
            # 10 updates per second
            time.sleep(0.1)
            

    def leaveEvent(self, event):
        QtGui.QApplication.restoreOverrideCursor()


    def mousePressEvent(self, event):
        logger.debug('FigureCanvasQTAggLocal.mousePressEvent: {}'
                      .format(event.button()))
        x = event.pos().x()
        # flip y so y=0 is bottom of canvas
        y = self.height() - event.pos().y()
        button = self.buttond.get(event.button())
        if button is not None:
            msg = (Msg.MOUSE_PRESS_EVENT, (x, y, button))
            self.child_conn.send(msg)
            
            
    def mouseDoubleClickEvent(self, event):
        logger.debug('FigureCanvasQTAggLocal.mouseDoubleClickEvent: {}'
                      .format(event.button()))
        x = event.pos().x()
        # flipy so y=0 is bottom of canvas
        y = self.height() - event.pos().y()
        button = self.buttond.get(event.button())
        if button is not None:
            msg = (Msg.MOUSE_DOUBLE_CLICK_EVENT, (x, y, button))
            self.child_conn.send(msg)


    def mouseMoveEvent(self, event):
#         if DEBUG:
#             print('FigureCanvasQTAggLocal.mouseMoveEvent: {}', (event.x(), event.y()))
        self.move_x = event.x()
        # flip y so y=0 is bottom of canvas
        self.move_y = self.height() - event.y()
        self.send_event.set()


    def mouseReleaseEvent(self, event):
        logger.debug('FigureCanvasQTAggLocal.mouseReleaseEvent: {}'
                      .format(event.button()))
        
        x = event.x()
        # flip y so y=0 is bottom of canvas
        y = self.height() - event.y()
        button = self.buttond.get(event.button())
        if button is not None:
            msg = (Msg.MOUSE_RELEASE_EVENT, (x, y, button))
            self.child_conn.send(msg)


    def resizeEvent(self, event):
        w = event.size().width()
        h = event.size().height()
                
        logger.debug("FigureCanvasQTAggLocal.resizeEvent : {}" 
                      .format((w, h)))            
        
        dpival = self.physicalDpiX()
        winch = w / dpival
        hinch = h / dpival
        
        self.figure.set_size_inches(winch, hinch)
        FigureCanvasAgg.resize_event(self)
        QtGui.QWidget.resizeEvent(self, event)
        
        wp_size = min([self.width(), self.height()]) / 5
        self.working_pixmap.resize(wp_size, wp_size)
        self.working_pixmap.move(self.width() - wp_size,
                                 self.height() - wp_size)
        
        # redrawing the plot window is a heavyweight operation, and we really
        # don't want to do it for every resize event.  so, upon a resize event,
        # start a 0.2 second timer. if there's another resize event before
        # it fires, cancel the timer and restart it.  otherwise, after 0.2
        # seconds, make the window redraw.  this minimizes redrawing and
        # makes the user experience much better, even though it's a stupid
        # hack because i can't (easily) stop the widget from recieveing
        # resize events during a resize.
        
        if self._resize_timer is not None:
            self._resize_timer.cancel()
            self._resize_timer = None
            
        def fire(self, width, height):
            self.resize_width = width
            self.resize_height = height
            self.send_event.set()
            self._resize_timer = None
            
        self._resize_timer = threading.Timer(0.2, fire, (self, winch, hinch))
        self._resize_timer.start()

        
    def paintEvent(self, e):
        """
        Copy the image from the buffer to the qt.drawable.
        In Qt, all drawing should be done inside of here when a widget is
        shown onscreen.
        """
        
        if self.buffer is None:
            return

        logger.debug('FigureCanvasQtAggLocal.paintEvent: '
                      .format(self, self.get_width_height()))
    
        if self.blit_buffer is None:
            
            # convert the Agg rendered image -> qImage
            qImage = QtGui.QImage(self.buffer, self.buffer_width,
                                  self.buffer_height,
                                  QtGui.QImage.Format_RGBA8888)
            # get the rectangle for the image
            rect = qImage.rect()
            p = QtGui.QPainter(self)
            # reset the image area of the canvas to be the back-ground color
            p.eraseRect(rect)
            # draw the rendered image on to the canvas
            p.drawPixmap(QtCore.QPoint(0, 0), QtGui.QPixmap.fromImage(qImage))

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

            p.end()
            self.blit_buffer = None
            
    def print_figure(self, *args, **kwargs):
        self.child_conn.send((Msg.PRINT, (args, kwargs)))



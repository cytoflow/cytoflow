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
cytoflowgui.matplotlib_backend_remote
-------------------------------------

A matplotlib backend that renders across a process boundary.  This file has
the "remote" canvas -- the Agg renderer into which pyplot.plot() renders.

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

import threading, logging, sys, traceback

import matplotlib.pyplot
from matplotlib.figure import Figure

#from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import MouseEvent

import numpy as np

# needed for pylab_setup
backend_version = "0.0.3"

from matplotlib.backend_bases import FigureManagerBase

logger = logging.getLogger(__name__)

class Msg(object):
    """
    Messages sent between the local and remote canvases.
    There is an identical class in `matplotlib_backend_local` because we
    don't want these two modules requiring one another
    """
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
    """Catch and log exceptions (with their tracebacks"""

    (exc_type, exc_value, tb) = sys.exc_info()

    err_string = traceback.format_exception_only(exc_type, exc_value)[0]
    err_loc = traceback.format_tb(tb)[-1]
    err_ctx = threading.current_thread().name
    
    logger.debug("Exception in {0}:\n{1}"
                  .format(err_ctx, "".join( traceback.format_exception(exc_type, exc_value, tb) )))
    
    
    logger.error("Error: {0}\nLocation: {1}Thread: {2}" \
                  .format(err_string, err_loc, err_ctx) )
    
class FigureCanvasAggRemote(FigureCanvasAgg):
    """
    The canvas the figure renders into in the remote process (ie, the one
    where someone is calling pyplot.plot()
    """
   
    def __init__(self, parent_conn, process_events, plot_lock, figure):      
        FigureCanvasAgg.__init__(self, figure)
        self._set_device_pixel_ratio(2.0)
        
        self.parent_conn = parent_conn
        self.process_events = process_events
        self.plot_lock = plot_lock
        
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
        
        self.working = False
        
        self.update_remote = threading.Event()
                
        t = threading.Thread(target = self.listen_for_local, 
                             name = "canvas listen", 
                             args = ())
        t.daemon = True 
        t.start()
        
        t = threading.Thread(target = self.send_to_local, 
                             name = "canvas send",
                             args=())
        t.daemon = True
        t.start()
        
    def listen_for_local(self): 
        """
        The main method for the thread that listens for messages from
        the local canvas
        """
        while self.parent_conn.poll(None):
            try:
                (msg, payload) = self.parent_conn.recv()
            except EOFError:
                return
            
            if msg != Msg.MOUSE_MOVE_EVENT:
                logger.debug("FigureCanvasAggRemote.listen_for_local :: {} {}"
                              .format(msg, payload))
                
            try:                                 
                if msg == Msg.RESIZE_EVENT:
                    with self.plot_lock:
                        (winch, hinch, dpi) = payload
                        self.figure.set_size_inches(winch, hinch)
                        matplotlib.rcParams['figure.dpi'] = dpi
                        # FigureCanvasAgg.resize_event(self)
                        self.draw()
                        
                elif msg == Msg.MOUSE_PRESS_EVENT:
                    (x, y, button) = payload
                    if self.process_events.is_set():
                        with self.plot_lock:
                            #FigureCanvasAgg.button_press_event(self, x, y, button)
                            MouseEvent("button_press_event", self, x, y, button, modifiers = None, guiEvent = None)._process()

                elif msg == Msg.MOUSE_DOUBLE_CLICK_EVENT:
                    (x, y, button) = payload
                    if self.process_events.is_set():
                        with self.plot_lock:
                            #FigureCanvasAgg.button_press_event(self, x, y, button, dblclick = True)
                            MouseEvent("button_press_event", self, x, y, button, dblclick = True, modifiers = None, guiEvent = None)._process()

                elif msg == Msg.MOUSE_RELEASE_EVENT:
                    (x, y, button) = payload
                    if self.process_events.is_set():
                        with self.plot_lock:
                            #FigureCanvasAgg.button_release_event(self, x, y, button)
                            MouseEvent("button_release_event", self, x, y, button, modifiers = None, guiEvent = None)._process()
                            
                elif msg == Msg.MOUSE_MOVE_EVENT:
                    (x, y) = payload
                    if self.process_events.is_set():
                        with self.plot_lock:
                            #FigureCanvasAgg.motion_notify_event(self, x, y)
                            MouseEvent("motion_notify_event", self, x, y, modifiers = None, guiEvent = None)._process()
                            
                elif msg == Msg.PRINT:
                    (args, kwargs) = payload
                    if self.process_events.is_set():
                        with self.plot_lock:
                            old_size = self.figure.get_size_inches()
                            
                            width = kwargs.pop('width')
                            height = kwargs.pop('height')
                            self.figure.set_size_inches(width, height)

                            FigureCanvasAgg.print_figure(self, *args, **kwargs)
                            
                            self.figure.set_size_inches(old_size[0], old_size[1])
                else:
                    raise RuntimeError("FigureCanvasAggRemote received bad message {}".format(msg))
            except Exception:
                log_exception()
            
    def send_to_local(self):
        """
        The main method for the thread that sends messages to the local canvas
        """
        
        while self.update_remote.wait():
            logger.debug("FigureCanvasAggRemote.send_to_local")
                
            self.update_remote.clear()
            
            if self.blit_buffer is not None:
                with self.blit_lock:
                    msg = (Msg.BLIT, (self.blit_buffer,
                                      self.blit_width,
                                      self.blit_height,
                                      self.blit_top,
                                      self.blit_left))
                self.parent_conn.send(msg)
                self.blit_buffer = None
            elif self.buffer is not None:
                with self.buffer_lock:
                    msg = (Msg.DRAW, (self.buffer,
                                      self.buffer_width, 
                                      self.buffer_height))
                self.parent_conn.send(msg)
                self.buffer = None
            
            msg = (Msg.WORKING, self.working)
            self.parent_conn.send(msg)

        
    def draw(self, *args, **kwargs):  # @UnusedVariable
        """
        When the canvas is instructed to draw itself, copy the Agg buffer out
        to a numpy array and send it to the local process.
        """
        logger.debug("FigureCanvasAggRemote.draw()")

        FigureCanvasAgg.draw(self)
            
        with self.buffer_lock:
            
            self.buffer = np.array(self.renderer.buffer_rgba())
                
            self.buffer_width = int(self.renderer.width)
            self.buffer_height = int(self.renderer.height)

        self.update_remote.set()
        

    def blit(self, bbox=None):
        """
        When instructed to blit a bounding box, copy the region in the bounding
        box to a numpy array and send it to the local canvas.
        """
        
        # If bbox is None, blit the entire canvas. Otherwise
        # blit only the area defined by the bbox.
        logger.debug("FigureCanvasAggRemote.blit() {}"
                     .format(bbox.extents))
        
        if bbox is None and self.figure:
            logger.info("bbox was none")
            return

        with self.blit_lock:
            l, b, r, t = bbox.extents

            w = int(r) - int(l)
            h = int(t) - int(b)
            t = int(b) + h
            l = int(l)
        
            region = self.copy_from_bbox(bbox)
            
            #self.blit_buffer = region.to_string_argb()
            self.blit_buffer = np.asarray(region)
            
            # convert from RGBA to ARGB
            self.blit_buffer = np.take(self.blit_buffer, [2, 1, 0, 3], axis = 2)
            self.blit_width = w
            self.blit_height = h
            self.blit_top = t
            self.blit_left = l
            
        self.update_remote.set()
        
        
    def set_working(self, working):
        self.working = working
        self.update_remote.set()
        
        
remote_canvas = None
singleton_lock = threading.Lock()

def new_figure_manager(num, *args, **kwargs):
    """
    Create a new figure manager instance.  This maintains the remote canvas as
    a singleton -- else, each new canvas would need a copy of the pipes, locks,
    etc.
    """
    
    global remote_canvas
    global singleton_lock
        
    logger.debug("mpl_multiprocess_backend.new_figure_manager()")
    
    # get the pipe connection
    parent_conn = kwargs.pop('parent_conn')

    # and the threading.Event for turning events on and off
    process_events = kwargs.pop('process_events')
    
    # and the plot lock
    plot_lock = kwargs.pop('plot_lock')

    # make a new figure
    FigureClass = kwargs.pop('FigureClass', Figure)
    new_fig = FigureClass(*args, **kwargs)
 
    with singleton_lock:
     
        # the canvas is a singleton.
        if not remote_canvas:
            remote_canvas = FigureCanvasAggRemote(parent_conn, process_events, plot_lock, new_fig)
            
        else:         
            old_fig = remote_canvas.figure
            new_fig.set_size_inches(old_fig.get_figwidth(), 
                                    old_fig.get_figheight())
            remote_canvas.figure = new_fig
        
    new_fig.set_canvas(remote_canvas)

    # close the current figure (to keep pyplot happy)
    matplotlib.pyplot.close()
 
    return FigureManagerBase(remote_canvas, num)

def show():
    logger.debug("mpl_multiprocess_backend.show")
    remote_canvas.draw()

# make sure pyplot uses the remote canvas
FigureCanvas = FigureCanvasAggRemote

# we don't need a figure manager with any more than default functionality
FigureManager = FigureManagerBase

# monkey-patch seaborn
def tight_layout(self, *args, **kwargs):
    pass

import seaborn.axisgrid  # @UnusedImport
seaborn.axisgrid.Grid.tight_layout = tight_layout

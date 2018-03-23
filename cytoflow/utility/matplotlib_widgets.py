#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
cytoflow.utility.matplotlib_widgets
-----------------------------------

Additional widgets to be used with matplotlib
'''

import time
from matplotlib.lines import Line2D
from matplotlib.widgets import AxesWidget, _SelectorWidget
from matplotlib.transforms import blended_transform_factory


class PolygonSelector(AxesWidget):
    """Selection polygon.
    
    The selected path can be used in conjunction with
    :func:`~matplotlib.path.Path.contains_point` to select data points
    from an image.
    
    Parameters
    ----------
    
    ax : :class:`~matplotlib.axes.Axes`
        The parent axes for the widget.
        
    callback : callable
        When the user double-clicks, the polygon closes and the ``callback`` 
        function is called and passed the vertices of the selected path.
    """

    def __init__(self, ax, callback=None, useblit=True):
        AxesWidget.__init__(self, ax)

        self.useblit = useblit and self.canvas.supports_blit
        self.verts = []
        self.drawing = False
        self.line = None
        self.callback = callback
        self.last_click_time = time.time()
        self.connect_event('button_press_event', self.onpress)
        self.connect_event('motion_notify_event', self.onmove)

    def onpress(self, event):
        if self.ignore(event):
            return

        if not self.drawing:
            # start over
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
            self.verts = [(event.xdata, event.ydata)]
            self.line = Line2D([event.xdata], [event.ydata], linestyle='-', color='black', lw=1)
            self.ax.add_line(self.line)
            self.drawing = True
        else:
            self.verts.append((event.xdata, event.ydata))
            self.line.set_data(list(zip(*self.verts)))
                
        if event.dblclick or (time.time() - self.last_click_time < 0.3):
            self.callback(self.verts)
            self.ax.lines.remove(self.line)
            self.drawing = False

        self.last_click_time = time.time()    

    def onmove(self, event):
        if self.ignore(event):
            return
        if not self.drawing:
            return
        if event.inaxes != self.ax:
            return

        self.line.set_data(list(zip(*(self.verts + [(event.xdata, event.ydata)]))))

        if self.useblit:
            self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.line)
            self.canvas.blit(self.ax.bbox)
        else:
            self.canvas.draw_idle()
            
class SpanSelector(_SelectorWidget):
    """
    Adapted from https://github.com/matplotlib/matplotlib/blob/master/lib/matplotlib/widgets.py

    Visually select a min/max range on a single axis and call a function with
    those values.
    
    To guarantee that the selector remains responsive, keep a reference to it.
    In order to turn off the SpanSelector, set `span_selector.active=False`. To
    turn it back on, set `span_selector.active=True`.
    
    Parameters
    ----------
    ax :  :class:`matplotlib.axes.Axes` object
    onselect : func(min, max), min/max are floats
    direction : "horizontal" or "vertical"
      The axis along which to draw the span selector
    minspan : float, default is None
     If selection is less than *minspan*, do not call *onselect*
    useblit : bool, default is False
      If True, use the backend-dependent blitting features for faster
      canvas updates.
    onmove_callback : func(min, max), min/max are floats, default is None
      Called on mouse move while the span is being selected
    span_stays : bool, default is False
      If True, the span stays visible after the mouse is released
    button : int or list of ints
      Determines which mouse buttons activate the span selector
        1 = left mouse button\n
        2 = center mouse button (scroll wheel)\n
        3 = right mouse button\n
    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> import matplotlib.widgets as mwidgets
    >>> fig, ax = plt.subplots()
    >>> ax.plot([1, 2, 3], [10, 50, 100])
    >>> def onselect(vmin, vmax):
            print(vmin, vmax)
    >>> span = mwidgets.SpanSelector(ax, onselect, 'horizontal')
    >>> fig.show()
    See also: :ref:`sphx_glr_gallery_widgets_span_selector.py`
    """

    def __init__(self, ax, onselect, minspan=None, useblit=False,
                 onmove_callback=None, span_stays=False,
                 button=None):

        _SelectorWidget.__init__(self, ax, onselect, useblit=useblit,
                                 button=button)

        self.rect = None
        self.pressv = None

        self.onmove_callback = onmove_callback
        self.minspan = minspan
        self.span_stays = span_stays

        # Needed when dragging out of axes
        self.prev = 0

        # Reset canvas so that `new_axes` connects events.
        self.canvas = None
        self.new_axes(ax)

    def new_axes(self, ax):
        """Set SpanSelector to operate on a new Axes"""
        self.ax = ax
        if self.canvas is not ax.figure.canvas:
            if self.canvas is not None:
                self.disconnect_events()
 
            self.canvas = ax.figure.canvas
            self.connect_default_events()

        trans = blended_transform_factory(self.ax.transData,
                                          self.ax.transAxes)
        
        self.low_line = Line2D((0, 0), (0, 1), 
                               transform = trans, 
                               visible = False,
                               color = 'blue',
                               linewidth = 2)
        
        self.high_line = Line2D((0, 0), (0, 1), 
                               transform = trans, 
                               visible = False,
                               color = 'blue',
                               linewidth = 2)
        
        self.hline = Line2D((0, 0), (0.5, 0.5),
                            transform = trans,
                            visible = False,
                            color = 'blue',
                            linewidth = 2)
        
        if self.span_stays:
            self.stay_low_line = Line2D((0, 0), (0, 1), 
                                   transform = trans, 
                                   visible = False,
                                   color = 'blue',
                                   linewidth = 2)
            
            self.stay_high_line = Line2D((0, 0), (0, 1), 
                                   transform = trans, 
                                   visible = False,
                                   color = 'blue',
                                   linewidth = 2)
            
            self.stay_hline = Line2D((0, 0), (0.5, 0.5),
                                transform = trans,
                                visible = False,
                                color = 'blue',
                                linewidth = 2)
            
            self.stay_low_line.set_animated(False)
            self.stay_high_line.set_animated(False)
            self.stay_hline.set_animated(False)
            
            self.ax.add_line(self.stay_low_line)
            self.ax.add_line(self.stay_high_line)
            self.ax.add_line(self.stay_hline)

        self.ax.add_line(self.low_line)
        self.ax.add_line(self.high_line)
        self.ax.add_line(self.hline)
        
        self.artists = [self.low_line, 
                        self.high_line, 
                        self.hline]


    def ignore(self, event):
        """return *True* if *event* should be ignored"""
        return _SelectorWidget.ignore(self, event) or not self.visible

    def _press(self, event):
        """on button press event"""
        self.low_line.set_visible(self.visible)
        self.high_line.set_visible(self.visible)
        self.hline.set_visible(self.visible)
        
        if self.span_stays:
            self.stay_low_line.set_visible(False)
            self.stay_high_line.set_visibile(False)
            self.stay_hline.set_visible(False)
            # really force a draw so that the stay rect is not in
            # the blit background
            if self.useblit:
                self.canvas.draw()

        xdata, _ = self._get_data(event)
        self.pressv = xdata

        self._set_span_xy(event)
        return False

    def _release(self, event):
        """on button release event"""
        if self.pressv is None:
            return
        self.buttonDown = False
        
        self.low_line.set_visible(False)
        self.high_line.set_visible(False)
        self.hline.set_visible(False)
 
        if self.span_stays:
            self.stay_high_line.set_xdata(self.high_line.get_xdata())
            self.stay_low_line.set_xdata(self.low_line.get_xdata())
            self.stay_hline.set_xdata(self.hline.get_xdata())
            
            self.stay_high_line.set_visible(True)
            self.stay_low_line.set_visible(True)
            self.stay_hline.set_visible(True)

        self.canvas.draw_idle()
        vmin = self.pressv
        xdata, _ = self._get_data(event)
        vmax = xdata or self.prev

        if vmin > vmax:
            vmin, vmax = vmax, vmin
        span = vmax - vmin
        if self.minspan is not None and span < self.minspan:
            return
        self.onselect(vmin, vmax)
        self.pressv = None
        return False

    def _onmove(self, event):
        """on motion notify event"""
        if self.pressv is None:
            return

        self._set_span_xy(event)

        if self.onmove_callback is not None:
            vmin = self.pressv
            xdata, _ = self._get_data(event)
            vmax = xdata or self.prev

            if vmin > vmax:
                vmin, vmax = vmax, vmin
            self.onmove_callback(vmin, vmax)

        self.update()
        return False

    def _set_span_xy(self, event):
        """Setting the span coordinates"""
        x, _ = self._get_data(event)
        if x is None:
            return

        self.prev = x
        v = x

        minv, maxv = v, self.pressv
        if minv > maxv:
            minv, maxv = maxv, minv
            
        self.low_line.set_xdata([minv, minv])
        self.high_line.set_xdata([maxv, maxv])
        self.hline.set_xdata([minv, maxv])

class Cursor(AxesWidget):
    """
    A horizontal and vertical line that spans the axes and moves with
    the pointer.  You can turn off the hline or vline respectively with
    the following attributes:

      *horizOn*
        Controls the visibility of the horizontal line

      *vertOn*
        Controls the visibility of the horizontal line

    and the visibility of the cursor itself with the *visible* attribute.

    For the cursor to remain responsive you must keep a reference to
    it.
    
    Adapted from https://github.com/matplotlib/matplotlib/blob/master/lib/matplotlib/widgets.py
    """
    def __init__(self, ax, horizOn=True, vertOn=True, useblit=False,
                 **lineprops):
        """
        Add a cursor to *ax*.  If ``useblit=True``, use the backend-
        dependent blitting features for faster updates (GTKAgg
        only for now).  *lineprops* is a dictionary of line properties.

        .. plot :: mpl_examples/widgets/cursor.py
        """
        # TODO: Is the GTKAgg limitation still true?
        AxesWidget.__init__(self, ax)

        self.connect_event('motion_notify_event', self.onmove)
        self.connect_event('draw_event', self.clear)

        self.visible = True
        self.horizOn = horizOn
        self.vertOn = vertOn
        self.useblit = useblit and self.canvas.supports_blit
        self.moved = False

        if self.useblit:
            lineprops['animated'] = True
        self.lineh = ax.axhline(ax.get_ybound()[0], visible=False, **lineprops)
        self.linev = ax.axvline(ax.get_xbound()[0], visible=False, **lineprops)

        self.background = None
        self.needclear = False

    def clear(self, event):
        """clear the cursor"""
        
        if self.ignore(event) or not self.moved:
            return
        if self.useblit:
            self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.linev.set_visible(False)
        self.lineh.set_visible(False)
        self.moved = False

    def onmove(self, event):
        """on mouse motion draw the cursor if visible"""
        
        if self.ignore(event):
            return
        if not self.canvas.widgetlock.available(self):
            return
        if event.inaxes != self.ax:
            self.linev.set_visible(False)
            self.lineh.set_visible(False)

            if self.needclear:
                self.canvas.draw()
                self.needclear = False
            return
        self.needclear = True
        if not self.visible:
            return
        self.linev.set_xdata((event.xdata, event.xdata))

        self.lineh.set_ydata((event.ydata, event.ydata))
        self.linev.set_visible(self.visible and self.vertOn)
        self.lineh.set_visible(self.visible and self.horizOn)

        self._update()

    def _update(self):
        
        if self.useblit:
            if self.background is not None:
                self.canvas.restore_region(self.background)
            self.ax.draw_artist(self.linev)
            self.ax.draw_artist(self.lineh)
            self.canvas.blit(self.ax.bbox)
        else:
            self.canvas.draw_idle()

        self.moved = True
        return False

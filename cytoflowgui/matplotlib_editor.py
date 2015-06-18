"""
From Pierre Haessig
https://gist.github.com/pierre-haessig/9838326

Qt adaptation of Gael Varoquaux's tutorial to integrate Matplotlib
http://docs.enthought.com/traitsui/tutorials/traits_ui_scientific_app.html#extending-traitsui-adding-a-matplotlib-figure-to-our-application

based on Qt-based code shared by Didrik Pinte, May 2012
http://markmail.org/message/z3hnoqruk56g2bje

adapted and tested to work with PySide from Anaconda in March 2014

with some bits from
http://matplotlib.org/examples/user_interfaces/embedding_in_qt4.html
"""

import matplotlib

# We want matplotlib to use our backend
matplotlib.use('module://matplotlib_backend')
from matplotlib_backend import FigureCanvas
from matplotlib.figure import Figure

from traits.api import Instance, Event

from pyface.widget import Widget
from pyface.qt import QtGui, QtCore

class MPLFigureEditor(Widget):
 
    id = 'edu.mit.synbio.matplotlib_editor'
    name = 'QT widget to display matplotlib plots'
 
    scrollable = True
    
    figure = Instance(Figure)
    _canvas = Instance(FigureCanvas)
    _layout = Instance(QtGui.QStackedLayout)
    
    clear = Event
    draw = Event    
 
    def __init__(self, parent, **traits):
        super(MPLFigureEditor, self).__init__(**traits)
        
        self.parent = parent
        self.control = QtGui.QWidget(parent)    # the layout that manages the pane
        self._layout = QtGui.QStackedLayout()
        self.control.setLayout(self._layout)
        
        self.on_trait_event(self._clear, 'clear', dispatch = 'ui')
        self.on_trait_event(self._draw, 'draw', dispatch = 'ui')
 
    def update_editor(self):
        pass
    
    def _clear(self):
        if self.figure:
            self.figure.clear()
        
    def _draw(self):
        if self.figure:
            self.figure.canvas.draw()
 
    # MAGIC: listens for a change in the 'figure' trait.
    def _figure_changed(self, old, new):
        if old:
            # remove the view's widget from the layout
            self._layout.takeAt(self._layout.indexOf(self._canvas))           
            self._canvas.setParent(None)
            del self._canvas
            
        if new:
            self._canvas = new.canvas
            self._layout.addWidget(self._canvas)
            self._canvas.setParent(self.control)

        
    


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

# We want matplotlib to use a QT backend
matplotlib.use('Qt4Agg')
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import matplotlib as mpl

import numpy as np
from traits.api import Float, Int, Any, Instance

from pyface.widget import Widget
from pyface.qt import QtGui

class MPLFigureEditor(Widget):
 
    id = 'edu.mit.synbio.matplotlib_editor'
    name = 'QT widget to display matplotlib plots'
 
    scrollable = True
    
    width = Float(5)
    height = Float(4)
    dpi = Int(100)
    
    control = Instance(FigureCanvas)
    figure = Instance(Figure)
    axes = Instance(Axes)
 
    def __init__(self, parent, **traits):
        super(MPLFigureEditor, self).__init__(**traits)
        self.control = self._create_canvas(parent)
 
    def update_editor(self):
        pass
 
    def _create_canvas(self, parent):
        """ Create the MPL canvas. """
        # matplotlib commands to create a canvas

        self.figure = Figure(figsize=(self.width, self.height),  
                             dpi=self.dpi)
        
        self.axes = self.figure.add_subplot(111)
        self.axes.hold(False)
        
        def f(t):
            return np.exp(-t) * np.cos(2*np.pi*t)

        t1 = np.arange(0.0, 5.0, 0.1)
        t2 = np.arange(0.0, 5.0, 0.02)
        self.axes.plot(t1, f(t1), 'bo', t2, f(t2), 'k')

        mpl_canvas = FigureCanvas(self.figure)
        mpl_canvas.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                 QtGui.QSizePolicy.Expanding)
        mpl_canvas.updateGeometry()

        return mpl_canvas
    


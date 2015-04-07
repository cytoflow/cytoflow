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
import new

# We want matplotlib to use a QT backend
matplotlib.use('Qt4Agg')
from matplotlib.backends.backend_qt4agg import FigureCanvas
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import numpy as np
from traits.api import Float, Int, Any, Instance, on_trait_change, Property

from pyface.widget import Widget
from pyface.qt import QtGui

class MPLFigureEditor(Widget):
 
    id = 'edu.mit.synbio.matplotlib_editor'
    name = 'QT widget to display matplotlib plots'
 
    scrollable = True
    
    figure = Instance(Figure)
    control = Instance(FigureCanvas)
    fig_num = Property
 
    def __init__(self, parent, **traits):
        super(MPLFigureEditor, self).__init__(**traits)
        plt.ion()
        self.control = self._create_canvas(parent)
 
    def update_editor(self):
        pass
 
    def _create_canvas(self, parent):
        """ Create the MPL canvas. """
        # matplotlib commands to create a canvas

        self.figure = plt.figure()
        # self.figure = plt.gcf()
        
        def f(t):
            return np.exp(-t) * np.cos(2*np.pi*t)

        t1 = np.arange(0.0, 5.0, 0.1)
        t2 = np.arange(0.0, 5.0, 0.02)
        plt.plot(t1, f(t1), 'bo', t2, f(t2), 'k')

        mpl_canvas = FigureCanvas(self.figure)

        return mpl_canvas
    
    # MAGIC: gets the value of the "fig_num" property
    def _get_fig_num(self):
        return self.figure.number
    
#     # MAGIC: listens for a change in the 'figure' trait.
#     def _figure_changed(self, old, new):
#         
#         if not isinstance(new, Figure) or not self.control:
#             return
# 
#         (w, h) = old.get_size_inches()
#         new.set_size_inches((w, h))        
#         #self.control.figure = new
#         #new.set_canvas(self.control)
#         
#         self.control.draw()
#         self.control.update()
#         
#         plt.close(old)
        
        
    


"""
From Pierre Haessig
https://gist.github.com/pierre-haessig/9838326

Qt adaptation of Gael Varoquaux's tutorial to integrate Matplotlib
http://docs.enthought.com/traitsui/tutorials/traits_ui_scientific_app.html#extending-traitsui-adding-a-matplotlib-figure-to-our-application

based on Qt-based code shared by Didrik Pinte, May 2012
http://markmail.org/message/z3hnoqruk56g2bje

adapted and tested to work with PySide from Anaconda in March 2014
"""

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import matplotlib

# We want matplotlib to use a QT backend
matplotlib.use('Qt4Agg')
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
 
from traits.api import Instance
from traitsui.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory

from pyface.widget import Widget

class MPLFigureEditor(Widget):
 
    id = 'edu.mit.synbio.matplotlib_editor'
    name = 'TraitsUI editor for matplotlib plots'
 
    scrollable = True
 
    def __init__(self, parent, **traits):
        super(MPLFigureEditor, self).__init__(**traits)
        self.control = self._create_canvas(parent)
        #self.set_tooltip()
 
    def update_editor(self):
        pass
 
    def _create_canvas(self, parent):
        """ Create the MPL canvas. """
        # matplotlib commands to create a canvas
        fig = plt.figure()
        ax = fig.add_axes([0.15, 0.1, 0.7, 0.3])
        ax.set_ylabel('volts')
        ax.set_title('a sine wave')
        mpl_canvas = FigureCanvas(fig)
        return mpl_canvas
    

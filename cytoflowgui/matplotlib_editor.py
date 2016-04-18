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

# import matplotlib

# We want matplotlib to use our backend
# matplotlib.use('module://matplotlib_local_backend')
from cytoflowgui.matplotlib_multiprocess_backend import FigureCanvasQTAggLocal
from matplotlib.figure import Figure

#from traits.api import Instance, Event

from pyface.widget import Widget
#from pyface.qt import QtGui

class MPLFigureEditor(Widget):
 
    id = 'edu.mit.synbio.matplotlib_editor'
    name = 'QT widget to display matplotlib plots'
 
    scrollable = True
    
    # canvas = Instance(FigureCanvas)
    #_layout = Instance(QtGui.QStackedLayout)
#     
#     clear = Event
#     draw = Event    
 
    def __init__(self, parent, **traits):
        super(MPLFigureEditor, self).__init__(**traits)
        
        self.parent = parent
        
        # initialize the local canvas with a dummy figure
        self.control = FigureCanvasQTAggLocal(Figure()) 
        #self.control = QtGui.QWidget(parent)    # the layout that manages the pane
        #self._layout = QtGui.QStackedLayout()
        #self.control.setLayout(self._layout)
#         
#         self.on_trait_event(self._clear, 'clear', dispatch = 'ui')
#         self.on_trait_event(self._draw, 'draw', dispatch = 'ui')
 
#     def update_editor(self):
#         pass
#     
#     def _clear(self):
#         if self.figure:
#             self.figure.clear()
#         
#     def _draw(self):
#         if self.figure:
#             self.figure.canvas.draw()
#  
#     # MAGIC: listens for a change in the 'figure' trait.
#     def _figure_changed(self, old, new):
#         if old:
#             # remove the view's widget from the layout
#             self._layout.takeAt(self._layout.indexOf(self._canvas))           
#             self._canvas.setParent(None)
#             del self._canvas
#             
#         if new:
#             self._canvas = new.canvas
#             self._layout.addWidget(self._canvas)
#             self._canvas.setParent(self.control)

        
    


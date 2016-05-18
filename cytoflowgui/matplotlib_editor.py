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

from traits.api import Str, Any, Instance
from traitsui.api import BasicEditorFactory
from traitsui.qt4.editor import Editor

from pyface.qt import QtCore, QtGui

from cytoflowgui.matplotlib_backend import FigureCanvasQTAggLocal
from matplotlib.figure import Figure

local_canvas = None  # singleton

class _MPLFigureEditor(Editor):
    
    # the currently selected notebook page
    selected = Any
    
    tab_widget = Instance(QtGui.QTabBar)
    
    def init(self, parent):
        global local_canvas
        
        # create a layout for the tab widget and the main view
        layout = QtGui.QVBoxLayout()
        self.control = QtGui.QWidget()
        self.control.setLayout(layout)
         
        # add the tab widget
        self.tab_widget = tab_widget = QtGui.QTabBar()
        QtCore.QObject.connect(tab_widget, 
                               QtCore.SIGNAL('currentChanged(int)'), 
                               self._tab_activated )
        tab_widget.setDocumentMode(True)
         
        layout.addWidget(tab_widget)
         
        # add the main plot
        if not local_canvas:
            local_canvas = FigureCanvasQTAggLocal(Figure())
            local_canvas.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                 QtGui.QSizePolicy.Expanding)
        layout.addWidget(local_canvas)
         
        # Set up the additional 'list items changed' event handler needed for
        # a list based trait. Note that we want to fire the update_editor_item
        # only when the items in the list change and not when intermediate
        # traits change. Therefore, replace "." by ":" in the extended_name
        # when setting up the listener.
        extended_name = self.extended_name.replace('.', ':')
        self.context_object.on_trait_change( self.update_editor_item,
                               extended_name + '_items?', dispatch = 'ui' )  
         
        # Set of selection synchronization:
        self.sync_value( self.factory.selected, 'selected' ) 
        


        
#     def save_figure(self, *args, **kwargs):
#         self.control.print_figure(*args, **kwargs)

    def update_editor(self):
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
            
        for v in self.value:
            self.tab_widget.addTab(str(v))


    def update_editor_item (self, event):
        """ Handles an update to some subset of the trait's list.
        """
        self.update_editor()

    
    def _tab_activated(self, idx):
        """ Handles a notebook tab being "activated" (i.e. clicked on) by the
            user.
        """
        if idx == -1:
            self.selected = None
        else:
            self.selected = self.value[idx]
    
    def dispose ( self ):
        """ Disposes of the contents of an editor.
        """
        self.context_object.on_trait_change( self.update_editor_item,
                                self.name + '_items?', remove = True )

        super(_MPLFigureEditor, self).dispose()
        
# editor factory
class MPLFigureEditor(BasicEditorFactory):
    klass = _MPLFigureEditor
    selected = Str


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
Created on Feb 11, 2015
@author: brian
"""

from traits.api import Instance, provides, Str, Any
from traitsui.api import BasicEditorFactory
from traitsui.qt4.editor import Editor

from pyface.qt import QtCore, QtGui
from pyface.tasks.api import TaskPane, ITaskPane

from cytoflowgui.matplotlib_backend import FigureCanvasQTAggLocal
from matplotlib.figure import Figure

@provides(ITaskPane)
class FlowTaskPane(TaskPane):
    """
    The center pane for the UI; contains the matplotlib canvas for plotting
    data views.  eventually, this will allow multiple views; for now, it's
    just one matplotlib canvas.
    """
    
    id = 'edu.mit.synbio.cytoflow.flow_task_pane'
    name = 'Cytometry Data Viewer'
    
    layout = Instance(QtGui.QVBoxLayout)
    canvas = Instance(FigureCanvasQTAggLocal)
        
    def create(self, parent):
        # create a layout for the tab widget and the main view
        self.layout = layout = QtGui.QVBoxLayout()
        self.control = QtGui.QWidget()
        self.control.setLayout(layout)
        
        tabs_ui = self.model.edit_traits(view = 'plot_view',
                                         kind = 'subpanel',
                                         parent = parent)
        self.layout.addWidget(tabs_ui.control) 
        
        # add the main plot
        self.canvas = FigureCanvasQTAggLocal(Figure(), self.model.child_matplotlib_conn)
        self.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding,
                                  QtGui.QSizePolicy.Expanding)
        layout.addWidget(self.canvas)

    def destroy(self):
        self.layout = self.control = None 
                  
    def export(self, filename):
        # TODO - eventually give a preview, allow changing size, dpi, aspect 
        # ratio, plot layout, etc.  at the moment, just export exactly what's
        # on the screen
        
        self.canvas.print_figure(filename, bbox_inches = 'tight')
    
class _TabListEditor(Editor):
    
    # the currently selected notebook page
    selected = Any
    
    def init(self, parent):        
        self.control = QtGui.QTabBar()
        QtCore.QObject.connect(self.control, 
                               QtCore.SIGNAL('currentChanged(int)'), 
                               self._tab_activated )
        self.control.setDocumentMode(True)
         
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


    def update_editor(self):
        while self.control.count() > 0:
            self.control.removeTab(0)
            
        for v in self.value:
            self.control.addTab(str(v))


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

        super(_TabListEditor, self).dispose()
        
# editor factory
class TabListEditor(BasicEditorFactory):
    klass = _TabListEditor
    selected = Str
        
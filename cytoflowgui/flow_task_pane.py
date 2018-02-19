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

"""
Created on Feb 11, 2015
@author: brian
"""
import sys

from traits.api import Instance, provides
from traitsui.editor_factory import EditorWithListFactory
from traitsui.qt4.enum_editor import BaseEditor as BaseEnumerationEditor
from traitsui.qt4.constants import ErrorColor

from pyface.qt import QtCore, QtGui
from pyface.tasks.api import TaskPane, ITaskPane

from cytoflowgui.matplotlib_backend import FigureCanvasQTAggLocal
from matplotlib.figure import Figure

@provides(ITaskPane)
class FlowTaskPane(TaskPane):
    """
    The center pane for the UI; contains the matplotlib canvas for plotting
    data views.
    """
    
    id = 'edu.mit.synbio.cytoflow.flow_task_pane'
    name = 'Cytometry Data Viewer'
    
    layout = Instance(QtGui.QVBoxLayout)                    # @UndefinedVariable
    canvas = Instance(FigureCanvasQTAggLocal)
        
    def create(self, parent):
        if self.canvas is not None:
            return
        
        # create a layout for the tab widget and the main view
        self.layout = layout = QtGui.QVBoxLayout()          # @UndefinedVariable
        self.control = QtGui.QWidget()                      # @UndefinedVariable
        self.control.setLayout(layout)
        
        tabs_ui = self.model.edit_traits(view = 'plot_view',
                                         kind = 'subpanel',
                                         parent = parent)
        self.layout.addWidget(tabs_ui.control) 
        
        # add the main plot
        self.canvas = FigureCanvasQTAggLocal(Figure(), self.model.child_matplotlib_conn)
        self.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding,  # @UndefinedVariable
                                  QtGui.QSizePolicy.Expanding)  # @UndefinedVariable
        layout.addWidget(self.canvas)

    def destroy(self):
        pass
#         self.layout = self.control = None 
                  
    def export(self, filename, **kwargs):      
        self.canvas.print_figure(filename, bbox_inches = 'tight', **kwargs)
    
class _TabListEditor(BaseEnumerationEditor):
    
    # the currently selected notebook page
#     selected = Any
    
    def init(self, parent):        
        super(_TabListEditor, self).init(parent)
        
        self.control = QtGui.QTabBar()                      # @UndefinedVariable
        self.control.setDocumentMode(True)  
        for name in self.names:
            self.control.addTab(str(name))
            
        QtCore.QObject.connect(self.control,                # @UndefinedVariable 
                               QtCore.SIGNAL('currentChanged(int)'), # @UndefinedVariable
                               self.update_object )


         
        # Set up the additional 'list items changed' event handler needed for
        # a list based trait. Note that we want to fire the update_editor_item
        # only when the items in the list change and not when intermediate
        # traits change. Therefore, replace "." by ":" in the extended_name
        # when setting up the listener.
#         extended_name = self.extended_name.replace('.', ':')
#         self.context_object.on_trait_change( self.update_editor_item,
#                                extended_name + '_items?', dispatch = 'ui' )  
#          
#         # Set of selection synchronization:
#         self.sync_value( self.factory.selected, 'selected' ) 


#     def update_editor(self):
#         while self.control.count() > 0:
#             self.control.removeTab(0)
#             
#         for v in self.value:
#             self.control.addTab(str(v))
#             
#         if not self.value:
#             self.selected = None


#     def update_editor_item (self, event):
#         """ Handles an update to some subset of the trait's list.
#         """
#         self.update_editor()

    def update_editor(self):
        """ Updates the editor when the object trait changes externally to the
            editor.
        """
        try:
            index = self.names.index(self.inverse_mapping[self.value])
            self.control.setCurrentIndex(index)
        except:
            self.control.setCurrentIndex(0)
            self.update_object(0)
    
    def update_object(self, idx):
        """ Handles a notebook tab being "activated" (i.e. clicked on) by the
            user.
        """
        if idx >= 0 and idx < len(self.names):
            name = self.names[idx]
            self.value = self.mapping[str(name)]
            
    def rebuild_editor(self):
        self.control.blockSignals(True)
        
        while self.control.count() > 0:
            self.control.removeTab(0)
             
        for name in self.names:
            self.control.addTab(str(name))
            
        self.control.blockSignals(False)
        self.update_editor()
        
    def error(self, excp):
        """ Handles an error that occurs while setting the object's trait value.
        """
        self._set_background(ErrorColor)
        
        

    
#     def dispose ( self ):
#         """ Disposes of the contents of an editor.
#         """
#         self.context_object.on_trait_change( self.update_editor_item,
#                                 self.name + '_items?', remove = True )
# 
#         super(_TabListEditor, self).dispose()
        
# editor factory
class TabListEditor(EditorWithListFactory):
    def _get_custom_editor_class(self):
        return _TabListEditor

        
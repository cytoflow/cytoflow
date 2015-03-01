"""
Created on Feb 26, 2015

@author: brian
"""

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import os
os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasTraits, provides, Instance, Str, Int, Property, List, \
                       Constant, Color, Bool, on_trait_change, Event

from traitsui.api import UI, Group, View, Item, TabularEditor
from traitsui.tabular_adapter import TabularAdapter
from traitsui.menu import Menu, Action
from traitsui.handler import Handler, Controller
from traitsui.qt4.tabular_editor import TabularEditorEvent

from pyface.i_dialog import IDialog
from pyface.api import Dialog

from pyface.qt import QtCore, QtGui
from pyface.qt.QtCore import pyqtSlot

from pyface.api import GUI, FileDialog, DirectoryDialog

import synbio_flowtools as sf

class ExperimentSetupAdapter(TabularAdapter):
    """ 
    The tabular adapter interfaces between the tabular editor and the data 
    being displayed. For more details, please refer to the traitsUI user guide. 
    """
    # List of (Column labels, Column ID).
    columns = [ ('Name',  'name')]
    
    column_menu = Menu(Action(name = "Add...", 
                              action = 'handler._on_add(object, column, info)',
                              enabled_when = 'column == 0'))
    
# The tabular editor works in conjunction with an adapter class, derived from 
# TabularAdapter. 
tabular_editor = TabularEditor(
    adapter    = ExperimentSetupAdapter(),
    operations = ['edit'],
    multi_select = True,
    auto_update = True,
    auto_resize = True,
    column_clicked = "col_clicked"
)

class Tube(HasTraits):
    """
    The model for a tube in an experiment.
    """
    
    # these are the traits that every tube has.  every other trait is
    # dynamically created.
    
    file = Str
    name = Str

class ExperimentSetup(HasTraits):
    """
    The model for the TabularEditor in the dialog
    """
    
    tubes = List(Tube)

    col_clicked = TabularEditorEvent

    view = View(
        Group(
            Item('tubes', 
                 id = 'table', 
                 editor = tabular_editor),
            show_labels = False
        ),
        title     = 'Experiment Setup',
        id        = 'edu.mit.synbio.experiment_table_editor',
        width     = 0.60,
        height    = 0.75,
        resizable = True
    )
    
class ExperimentHandler(Controller):
        
    def _on_add(self, experiment, column, uiinfo):
        print "add handled"
        print column
        
@provides(IDialog)
class ExperimentSetupDialog(Dialog):
    """
    Another center pane; this one for setting up an experiment: loading
    FCS files and specifying metadata.  Centered around a table editor.
    """

    id = 'edu.mit.synbio.experiment_setup_dialog'
    name = 'Cytometry Experiment Setup'
    style = 'modal'
    
    experiment = Instance(sf.Experiment)
    model = Instance(ExperimentSetup)
    handler = Instance(Handler)
    ui = Instance(UI)
        
        
    def _create_buttons(self, parent):
        """ 
        Create the buttons at the bottom of the dialog box.
        
        We're overriding (and stealing code from) pyface.qt._create_buttons in
        order to add "Add tube.... " and "Add plate..." buttons.
        """
         
        #buttons = QtGui.QDialogButtonBox()
        buttons = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()
        
        btn_condition = QtGui.QPushButton("Add condition...")
        layout.addWidget(btn_condition)
        QtCore.QObject.connect(btn_condition, QtCore.SIGNAL('clicked()'),
                               self._add_condition)
        
        btn_tube = QtGui.QPushButton("Add tubes...")
        layout.addWidget(btn_tube)
        QtCore.QObject.connect(btn_tube, QtCore.SIGNAL('clicked()'),
                               self._add_tube)
        
        btn_plate = QtGui.QPushButton("Add plate...")
        layout.addWidget(btn_plate)
        QtCore.QObject.connect(btn_plate, QtCore.SIGNAL('clicked()'),
                               self._add_plate)
        
        layout.addStretch()

        # 'OK' button.
        btn_ok = QtGui.QPushButton("OK")
        btn_ok.setDefault(True)
        layout.addWidget(btn_ok)
        QtCore.QObject.connect(btn_ok, QtCore.SIGNAL('clicked()'),
                               self.control, QtCore.SLOT('accept()'))

        # 'Cancel' button.
        btn_cancel = QtGui.QPushButton("Cancel")
        layout.addWidget(btn_cancel)
        QtCore.QObject.connect(btn_cancel, QtCore.SIGNAL('clicked()'),
                               self.control, QtCore.SLOT('reject()'))   
        
        # add the button container to the widget     
        buttons.setLayout(layout)
        return buttons
    
    def _create_dialog_area(self, parent):
        
        self.model = ExperimentSetup()
        self.handler = ExperimentHandler()
        self.ui = self.model.edit_traits(kind='subpanel', parent=parent, 
                                         handler = self.handler)       
        return self.ui.control
    
    def destroy(self):
        self.ui.dispose()
        self.ui = None
        
        super(Dialog, self).destroy()
        
        
    class AddConditionDialog(Dialog):
        
        ok_label = "OK"
        cancel_label = "Cancel"
        
        new_condition_name = Str
        
        
        def _create_content(self, parent):
            pass
    
    def _add_condition(self):
        pass
    
    def _add_tube(self):
        
        print self.model.col_clicked
        return
        
        fd = FileDialog()
        fd.wildcard = "Flow cytometry files (*.fcs)|*.fcs|"
        fd.action = 'open files'
        fd.open()
        
        print fd.paths
        
    def _add_plate(self):
        print "add plate"
        print type(tabular_editor)
        
        Tube.add_class_trait('Dox', Bool)
        
        c2 = list(tabular_editor.adapter.columns)
        c2.append(('Dox',  'dox'))
        tabular_editor.adapter.columns = c2
    
if __name__ == '__main__':

    gui = GUI()
    
    # create a Task and add it to a TaskWindow
    d = ExperimentSetupDialog()
    d.open()
    
    gui.start_event_loop()        
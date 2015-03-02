"""
Created on Feb 26, 2015

@author: brian
"""

from traits.etsconfig.api import ETSConfig
from FlowCytometryTools.core.containers import FCMeasurement, FCPlate
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
from pyface.constant import OK as PyfaceOK

from pyface.api import GUI, FileDialog, DirectoryDialog

import synbio_flowtools as sf

class ExperimentSetupAdapter(TabularAdapter):
    """ 
    The tabular adapter interfaces between the tabular editor and the data 
    being displayed. For more details, please refer to the traitsUI user guide. 
    """
    # List of (Column labels, Column ID).
    columns = [ ('Name',  'Name')]
    
    column_menu = Menu(Action(name = "Add...", 
                              action = 'handler._on_add(object, column, info)',
                              enabled_when = 'column == 0'))
    
class Tube(HasTraits):
    """
    The model for a tube in an experiment.
    """
    
    # these are the traits that every tube has.  every other trait is
    # dynamically created.
    
    File = Str
    Name = Str

class ExperimentSetup(HasTraits):
    """
    The model for the TabularEditor in the dialog
    """
    
    tubes = List(Tube)

    # traits to communicate with the TabularEditor
    col_clicked = Instance('TabularEditorEvent')
    update = Bool
    refresh = Bool
    
    tube_metadata = {}
    
    adapter = ExperimentSetupAdapter()

    view = View(
        Group(
            Item('tubes', 
                 id = 'table', 
                 editor = TabularEditor(adapter = adapter,
                                        operations = ['edit'],
                                        multi_select = True,
                                        auto_update = True,
                                        auto_resize = True,
                                        column_clicked = "col_clicked",
                                        update = "update",
                                        refresh = "refresh")),
            show_labels = False
        ),
        title     = 'Experiment Setup',
        id        = 'edu.mit.synbio.experiment_table_editor',
        width     = 0.60,
        height    = 0.75,
        resizable = True
    )
    
class ExperimentHandler(Controller):
    
    dialog = Instance(IDialog)
    
    def init(self, info):
        # connect the model trait change events to the controller methods
        self.model.on_trait_change(self._on_col_clicked, 'col_clicked')
        return True
    
    def _on_ok(self):
        print "clicked okay"
        # TODO - validate input
        self.dialog.control.accept()
        
    def _on_add(self, experiment, column, uiinfo):
        print "add handled"
        print column
        
    def _on_col_clicked(self, click_event): 
        """
        When a column is clicked, sort the table values by that column.
        """
        
        sort_trait = self.model.adapter.columns[click_event.column][1]
        self.model.tubes.sort(key = lambda x: x.trait_get([sort_trait]))
        
    def _on_add_tubes(self):
        """
        Handle "Add tubes..." button.  Add tubes to the experiment.
        """
        
        file_dialog = FileDialog()
        file_dialog.wildcard = "Flow cytometry files (*.fcs)|*.fcs|"
        file_dialog.action = 'open files'
        file_dialog.open()
        
        if file_dialog.return_code != PyfaceOK:
            return
        
        for path in file_dialog.paths:
            tube = Tube(file = path)
            fcs = FCMeasurement(ID='new tube', datafile = path)
            tube.Name = fcs.meta['$SRC']
            self.model.tubes.append(tube)
    
    def _on_add_plate(self):

        dir_dialog = DirectoryDialog()
        dir_dialog.new_directory = False
        dir_dialog.open()
        
        if dir_dialog.return_code != PyfaceOK:
            return
                
        self._add_metadata("Row", Str)
        self._add_metadata("Col", Int)
        
        # TODO - error handling!
        # TODO - allow for different file name prototypes or manufacturers
        plate = FCPlate.from_dir(ID='new plate', 
                                 path=dir_dialog.path,
                                 parser = 'name',
                                 ID_kwargs={'pre':'_',
                                            'post':'_'} )
        
        for well_name in plate.data:
            well_data = plate[well_name]
            tube = Tube(file = well_data.datafile,
                        Row = well_data.position['new plate'][0],
                        Col = well_data.position['new plate'][1],
                        Name = well_data.meta['$SRC'])
            self.model.tubes.append(tube)
        
    def _add_metadata(self, meta_name, meta_type):
        
        if not meta_name in self.model.tube_metadata:
            Tube.add_class_trait(meta_name, meta_type)
            self.model.tube_metadata[meta_name] = meta_type
            
            # should be able to do this....
            #self.model.adapter.columns.append( (meta_name, meta_name))
            #self.model.refresh = True

            # ...but instead have to force the adapter to update label_map
            c = self.model.adapter.columns
            c.append( (meta_name, meta_name) )
            self.model.adapter.columns = c
            
            # TODO - fix the column width weirdness.
        
@provides(IDialog)
class ExperimentSetupDialog(Dialog):
    """
    A dialog for setting up an experiment: loading FCS files and specifying 
    metadata.  Centered around a table editor.
    """

    id = 'edu.mit.synbio.experiment_setup_dialog'
    name = 'Cytometry Experiment Setup'
    style = 'modal'
    
    model = Instance(ExperimentSetup)
    handler = Instance(Handler)
    ui = Instance(UI)
    
    def _create(self):
        """ 
        Creates the window's widget hierarchy. 
        
        Need to override this protected interface so we can instantiate the
        model and controller.
        """
        
        self.model = ExperimentSetup()
        self.handler = ExperimentHandler(model = self.model, dialog = self)

        super(ExperimentSetupDialog, self)._create()
    
        
    def _create_buttons(self, parent):
        """ 
        Create the buttons at the bottom of the dialog box.
        
        We're overriding (and stealing code from) pyface.qt._create_buttons in
        order to add "Add tube.... " and "Add plate..." buttons.
        """
         
        #buttons = QtGui.QDialogButtonBox()
        buttons = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()
        
        '''
        btn_condition = QtGui.QPushButton("Add condition...")
        layout.addWidget(btn_condition)
        QtCore.QObject.connect(btn_condition, QtCore.SIGNAL('clicked()'),
                               handler._add_condition)
        '''
        
        btn_tube = QtGui.QPushButton("Add tubes...")
        layout.addWidget(btn_tube)
        QtCore.QObject.connect(btn_tube, QtCore.SIGNAL('clicked()'),
                               self.handler._on_add_tubes)
        
        btn_plate = QtGui.QPushButton("Add plate...")
        layout.addWidget(btn_plate)
        QtCore.QObject.connect(btn_plate, QtCore.SIGNAL('clicked()'),
                               self.handler._on_add_plate)
        
        layout.addStretch()

        # 'OK' button.
        btn_ok = QtGui.QPushButton("OK")
        btn_ok.setDefault(True)
        layout.addWidget(btn_ok)
        QtCore.QObject.connect(btn_ok, QtCore.SIGNAL('clicked()'),
                               self.handler._on_ok)
                               #self.control, QtCore.SLOT('accept()'))

        # 'Cancel' button.
        btn_cancel = QtGui.QPushButton("Cancel")
        layout.addWidget(btn_cancel)
        QtCore.QObject.connect(btn_cancel, QtCore.SIGNAL('clicked()'),
                               self.control, QtCore.SLOT('reject()'))   
        
        # add the button container to the widget     
        buttons.setLayout(layout)
        return buttons
    
    def _create_dialog_area(self, parent):
        
        self.ui = self.model.edit_traits(kind='subpanel', 
                                         parent=parent, 
                                         handler=self.handler)       
        return self.ui.control
    
    def destroy(self):
        self.ui.dispose()
        self.ui = None
        
        super(Dialog, self).destroy()
    
if __name__ == '__main__':

    gui = GUI()
    
    # create a Task and add it to a TaskWindow
    d = ExperimentSetupDialog()
    d.open()
    
    gui.start_event_loop()        
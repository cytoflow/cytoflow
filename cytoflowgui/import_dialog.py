"""
Created on Feb 26, 2015

@author: brian
"""
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"
    
from traits.api import HasTraits, provides, Instance, Str, Int, List, \
                       Bool, Enum, Float, DelegatesTo, Property, CStr, Dict, \
                       Trait
                       
from traitsui.api import UI, Group, View, Item, TableEditor, OKCancelButtons, \
                         Controller

from traitsui.qt4.table_editor import TableEditor as TableEditorQt

from pyface.i_dialog import IDialog
from pyface.api import Dialog, GUI, FileDialog

from pyface.qt import QtCore, QtGui
from pyface.constant import OK as PyfaceOK

from pyface.ui.qt4.directory_dialog import DirectoryDialog as QtDirectoryDialog

from FlowCytometryTools.core.containers import FCMeasurement, FCPlate
from traitsui.table_column import ObjectColumn
from collections import Counter
from cytoflow.operations.import_op import Tube, LogFloat

class PlateDirectoryDialog(QtDirectoryDialog):
    """
    A custom open file dialog for opening plates, so we can specify different
    file name --> plate position mappings.
    """
    
    def _create_control(self, parent):
        self.dlg = QtGui.QFileDialog(parent, self.title, self.default_path)
    
        self.dlg.setViewMode(QtGui.QFileDialog.Detail | QtGui.QFileDialog.ShowDirsOnly)
        self.dlg.setFileMode(QtGui.QFileDialog.Directory)
    
        self.dlg.setNameFilters(["one", "two"])
        self.dlg.setReadOnly(True)
    
        return self.dlg
    
    def selectedNameFilter(self):
        return self.dlg.selectedNameFilter()
    
    
class ExperimentColumn(ObjectColumn):
    
    # override ObjectColumn.get_cell_color
    def get_cell_color(self, obj):
        if(obj._parent.tubes_counter[object] > 1):
            return QtGui.QColor('lightpink')
        else:
            return super(ObjectColumn, self).get_cell_color(object)
        
    
class ExperimentDialogModel(HasTraits):
 
    # the tubes
    tubes = List(Tube)
    
    # the traits on the tubes that are experimental conditions
    conditions = List(Str)
    
    #the rest is for communicating with the View
    
    # a collections.Counter that keeps track of duplicates for us.  rebuilt
    # whenever the Tube elements of self.tubes changes
    tubes_counter = Property(depends_on = 'tubes[]')
    
    # traits to communicate with the TabularEditor
    update = Bool
    refresh = Bool
    selected = List
    
    view = View(
            Group(
                Item(name = 'tubes', 
                     id = 'table', 
                     editor = TableEditor(editable = True,
                                          sortable = True,
                                          auto_size = True,
                                          configurable = False,
                                          selection_mode = 'cells',
                                          selected = 'selected',
                                          columns = [ExperimentColumn(name = 'Name')],
                                          ),
                     enabled_when = "object.tubes"),
                show_labels = False
            ),
            title     = 'Experiment Setup',
            id        = 'edu.mit.synbio.experiment_table_editor',
            width     = 0.60,
            height    = 0.75,
            resizable = True
        )
    
    ## i'd love to cache this, but it screws up the coloring stuff  :-/
    def _get_tubes_counter(self):
        return Counter(self.tubes)

class ExperimentDialogHandler(Controller):

    # keep around a ref to the underlying widget so we can add columns dynamically
    table_editor = Instance(TableEditorQt)
    
    def init_info(self, info):
        
        # set the parent model object for any preexisting tubes
        for tube in self.model.tubes:
            tube._parent = self.model

        for tube in self.model.tubes:
            for cond in self.model.conditions:
                assert(tube.trait(cond) is not None)

        # and make sure the Tube class traits are synchronized with the 
        # instance traits (handles the case where we unpicked a bunch of
        # Tube instances)
                
#         tube = self.model.tubes[0]
#         for trait_name in tube.trait_names(transient = lambda x: x is not True):
#             trait = tube.trait(trait_name)
#             if not trait_name in Tube.class_trait_names():
#                 Tube.add_class_trait(trait_name, trait) 
            
        
        
            
        Controller.init_info(self, info)
    
    def closed(self, info, is_ok):
        for tube in self.model.tubes:
            tube.on_trait_change(self._try_multiedit, '+', remove = True)
        
    def _on_delete_column(self, obj, column, info):
        # TODO - be able to remove traits..... ?
        pass
        
    def _on_add_condition(self):
        """
        Add a new condition.  Use TraitsUI to make a simple dialog box.
        """
        
        class NewTrait(HasTraits):    
            condition_name = CStr
            condition_type = Enum(["String", "Number", "Number (Log)", "True/False"])
    
            view = View(Item(name = 'condition_name'),
                        Item(name = 'condition_type'),
                        buttons = OKCancelButtons,
                        title = "Add a trait",
                        close_result = False)
        
        new_trait = NewTrait()
        new_trait.edit_traits(kind = 'modal')
        
        if not new_trait.condition_name: 
            return
        
        name = new_trait.condition_name
        
        if new_trait.condition_type == "String":
            self._add_metadata(name, name + " (String)", Str(condition = True))
        elif new_trait.condition_type == "Number":
            self._add_metadata(name, name + " (Number)", Float(condition = True))
        elif new_trait.condition_type == "Number (Log)":
            self._add_metadata(name, name + " (Log)", LogFloat(condition = True))
        else:
            self._add_metadata(name, name + " (T/F)", Bool(condition = True))       
        
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
            tube = Tube(File = path)
            tube._parent = self.model
            fcs = FCMeasurement(ID='new tube', datafile = path)
            tube.Name = fcs.meta['$SRC']
            tube.on_trait_change(self._try_multiedit, '+')
            self.model.tubes.append(tube)
    
    def _on_add_plate(self):
        # TODO - add alternate manufacturer's plate types (to the name filters)
        
        dir_dialog = PlateDirectoryDialog()
        dir_dialog.open()
        
        print dir_dialog.selectedNameFilter()
        
        if dir_dialog.return_code != PyfaceOK:
            return
                
        self._add_metadata("Row", "Row", Str(condition = False))
        self._add_metadata("Col", "Col", Int(condition = False))
        
        # TODO - error handling!
        # TODO - allow for different file name prototypes or manufacturers
        plate = FCPlate.from_dir(ID='new plate', 
                                 path=dir_dialog.path,
                                 parser = 'name',
                                 ID_kwargs={'pre':'_',
                                            'post':'_'} )
        
        for well_name in plate.data:
            well_data = plate[well_name]
            tube = Tube(File = well_data.datafile,
                        Row = well_data.position['new plate'][0],
                        Col = well_data.position['new plate'][1],
                        Name = well_data.meta['$SRC'])
            tube._parent = self.model
            tube.on_trait_change(self._try_multiedit, '+')
            self.model.tubes.append(tube)
            
    def _try_multiedit(self, obj, name, old, new):
        """
        See if there are multiple elements selected when a tube's trait changes
        
        and if so, edit the same trait for all the selected tubes.
        """
                
        for tube, trait_name in self.model.selected:
            if tube != obj:
                tube.trait_set( **dict([(trait_name, new)]))
        
    def _add_metadata(self, meta_name, column_name, meta_type):
        """
        Add a new condition
        """
        
        if not meta_name in self.model.conditions:
            self.model.conditions.append(meta_name)
            for tube in self.model.tubes:
                tube.add_trait(meta_name, meta_type)     
                tube.on_trait_change(self._try_multiedit, meta_name)
                
            self.table_editor.columns.append(ExperimentColumn(name = meta_name,
                                                              label = column_name))
                
    def _remove_metadata(self, meta_name, column_name, meta_type):
        # TODO
        pass
        
@provides(IDialog)
class ExperimentDialog(Dialog):
    """
    A dialog for setting up an experiment: loading FCS files and specifying 
    metadata.  Centered around a table editor.
    """

    id = 'edu.mit.synbio.experiment_setup_dialog'
    name = 'Cytometry Experiment Setup'
    
    style = 'modal'
    title = 'Experiment setup'

    handler = Instance(ExperimentDialogHandler, 
                       kw = {'model' : ExperimentDialogModel()})
    model = DelegatesTo('handler')

    ui = Instance(UI)
        
    def _create_buttons(self, parent):
        """ 
        Create the buttons at the bottom of the dialog box.
        
        We're overriding (and stealing code from) pyface.qt._create_buttons in
        order to add "Add tube.... " and "Add plate..." buttons.
        """
         
        buttons = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()
        
        btn_tube = QtGui.QPushButton("Add tubes...")
        layout.addWidget(btn_tube)
        QtCore.QObject.connect(btn_tube, QtCore.SIGNAL('clicked()'),
                               self.handler._on_add_tubes)
        
        btn_plate = QtGui.QPushButton("Add plate...")
        layout.addWidget(btn_plate)
        QtCore.QObject.connect(btn_plate, QtCore.SIGNAL('clicked()'),
                               self.handler._on_add_plate)
        
        btn_add_cond = QtGui.QPushButton("Add condition...")
        layout.addWidget(btn_add_cond)
        QtCore.QObject.connect(btn_add_cond, QtCore.SIGNAL('clicked()'),
                               self.handler._on_add_condition)
        
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
        
        self.ui = self.model.edit_traits(kind='subpanel', 
                                         parent=parent, 
                                         handler=self.handler)   
        
        # need to keep a reference to the table editor so we can dynamically
        # add columns to it.
        self.handler.table_editor = self.ui.get_editors('tubes')[0]
        
        # and if the Tube class already has traits defined, add them to the 
        # table editor
        ext_traits = Tube.class_trait_names(condition = True,
                                            transient = lambda x: x is not True)
        for trait in ext_traits:
            self.handler.table_editor.columns.append(ExperimentColumn(name = trait,
                                                                      label = trait))
  
        return self.ui.control
    
    def destroy(self):
        self.ui.dispose()
        self.ui = None
        
        super(Dialog, self).destroy()
        
    
if __name__ == '__main__':

    gui = GUI()
    
    # create a Task and add it to a TaskWindow
    d = ExperimentDialog()
    d.size = (550, 500)
    d.open()
    
    gui.start_event_loop()        
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
                       Bool, Enum, Float, DelegatesTo, Property, CStr
                       
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

def not_true ( value ):
    return (value is not True)

def not_false ( value ):
    return (value is not False)

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
    """
    The model for the Experiment setup dialog.
    
    This model depends on duck-typing ("if it walks like a duck, and quacks
    like a duck...").  Because we want to use all of the TableEditor's nice
    features, each row needs to be an instance, and each column a Trait.
    So, each Tube instance represents a single tube, and each experimental
    condition (as well as the tube name, its file, and optional plate row and 
    col) are traits. These traits are dynamically added to Tube INSTANCES 
    (NOT THE TUBE CLASS.)  Then, we add appropriate columns to the table editor
    to access these traits.
    
    This is slightly complicated by the fact that there are two different
    kinds of traits we want to keep track of: traits that specify experimental
    conditions (inducer concentration, time point, etc.) and other things
    (file name, tube name, etc.).  We differentiate them because we enforce
    the invariant that each tube MUST have a unique combination of experimental
    conditions.  I used to do this with trait metadata (seems like the right
    thing) .... but trait metadata on dynamic traits (both instance and
    class) doesn't survive pickling.  >.>
    
    So: we keep a separate list of traits that are experimental conditions.
    Every 'public' trait (doesn't start with '_') is given a column in the
    editor; only those that are in the conditions list are considered for tests
    of equality (to make sure combinations of experimental conditions are 
    unique.)
    
    And of course, the 'transient' flag controls whether the trait is serialized
    or not.
    """
    
    # the tubes.  this is the model; the rest is for communicating with the View
    tubes = List(Tube)
    
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
            self._add_metadata(name, name + " (String)", Str, condition = True)
        elif new_trait.condition_type == "Number":
            self._add_metadata(name, name + " (Number)", Float, condition = True)
        elif new_trait.condition_type == "Number (Log)":
            self._add_metadata(name, name + " (Log)", LogFloat, condition = True)
        else:
            self._add_metadata(name, name + " (T/F)", Bool, condition = True)       
        
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
            tube = Tube(_file = path)
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
            tube = Tube(_file = well_data.datafile,
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
        
    def _add_metadata(self, name, label, klass, condition):
        """
        Add a new tube metadata
        """
        
        traits = self.model.tubes[0].trait_names(transient = not_true)
            
        if not name in traits:
            for tube in self.model.tubes:
                tube.add_metadata(name, klass, klass.default, condition)
                tube.on_trait_change(self._try_multiedit, name)    

            self.table_editor.columns.append(ExperimentColumn(name = name,
                                                              label = label))
                
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
        if len(self.model.tubes) > 0:
            trait_to_col = {"Str" : " (String)",
                            "Float" : " (Number)",
                            "LogFloat" : " (Log)",
                            "Bool" : " (T/F)",
                            "Int" : " (Int)"}
            
            trait_names = self.model.tubes[0].trait_names(transient = not_true,
                                                          show = not_false)
            for trait_name in trait_names:
                if trait_name.startswith("_") or trait_name == "Name":
                    continue
                trait = self.model.tubes[0].trait(trait_name)
                trait_type = trait.trait_type.__class__.__name__
                col_name = trait_name + trait_to_col[trait_type]
                self.handler.table_editor.columns.append(ExperimentColumn(name = trait_name,
                                                                          label = col_name))
      
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
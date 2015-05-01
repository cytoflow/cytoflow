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
                       Bool, Enum, Float, DelegatesTo, Property, CStr, \
                       HasStrictTraits
                       
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

from cytoflow import Tube as CytoflowTube

def not_true ( value ):
    return (value is not True)

def not_false ( value ):
    return (value is not False)

class LogFloat(Float):
    """
    A trait to represent a numeric condition on a log scale.
    
    Since I can't figure out how to add metadata to a trait class (just an
    instance), we'll subclass it instead.  Don't need to override anything;
    all we're really looking to change is the name.
    """

class Tube(HasStrictTraits):
    """
    The model for a tube in an experiment.
    
    I originally wanted to make the Tube in the ImportDialog and the Tube in
    the ImportOp the same, but that fell apart when I tried to implement
    serialization (dynamic traits don't survive pickling.)  (well, their values
    do, but neither the trait type nor the metadata do.)
    
    Oh well.
        
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
    conditions.  We do this with trait metadata: "condition == True" means 
    "is an experimental condition" (everything but File, Name, Row, Column, 
    _parent).
    
    We also use the "transient" flag to specify traits that shouldn't be 
    displayed in the editor.  This matches well with the traits that
    every HasTraits-derived class has by default (all of which are transient.)
    """
    
    # these are the traits that every tube has.  every other trait is
    # dynamically created. 

    # the tube or well name.  pulled from FCS metadata
    Name = Str
    
    # the file name.
    _file = Str(transient = True)
    
    # need a link to the model; needed for row coloring
    _parent = Instance("ExperimentDialogModel", transient = True)
    
    def __hash__(self):
        ret = int(0)
        for trait in self.trait_names(condition = True):
            if not ret:
                ret = hash(self.trait_get(trait)[trait])
            else:
                ret = ret ^ hash(self.trait_get(trait)[trait])
                
        return ret
    
    def __eq__(self, other):
        for trait in self.trait_names(condition = True):
            if not self.trait_get(trait)[trait] == other.trait_get(trait)[trait]:
                return False
                
        return True

    
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
    
    def init_model(self, op):
        dtype_to_trait = {"category" : Str,
                          "float" : Float,
                          "log" : LogFloat,
                          "bool" : Bool,
                          "int" : Int}
        
        has_row = any(tube.row for tube in op.tubes)
        has_col = any(tube.col for tube in op.tubes)
        for op_tube in op.tubes:
            tube = Tube(Name = op_tube.name,
                        _file = op_tube.file)
            if has_row:
                tube.add_trait("Row", Str)
                tube.Row = op_tube.row
            if has_col:
                tube.add_trait("Col", Str)
                
            for condition in op_tube.conditions:
                condition_dtype = op.conditions[condition]
                condition_trait = \
                    dtype_to_trait[condition_dtype](condition = True)
                tube.add_trait(condition, condition_trait)
            tube.trait_set(**op_tube.conditions)
    
    def update_import_op(self, op):
        trait_to_dtype = {"Str" : "category",
                          "Float" : "float",
                          "LogFloat" : "log",
                          "Bool" : "bool",
                          "Int" : "int"}
        
        op.conditions.clear()
        for trait_name in self.tubes[0].trait_names(condition = True):
            trait = self.tubes[0].trait(trait_name)
            trait_type = trait.trait_type.__class__.__name__
            op.conditions[trait_name] = trait_to_dtype[trait_type]
            
        for tube in self.tubes:
            op_tube = CytoflowTube(name = tube.Name,
                                   file = tube._file)
            
            if "Row" in tube.trait_names():
                op_tube.row = tube.Row
                
            if "Col" in tube.trait_names():
                op_tube.col = tube.Col
                
            op_tube.conditions = tube.trait_get(condition = True)
            
            # AFAICT this is going to cause the op to reload THE ENTIRE
            # SET each time a tube is added.  >.>
            # TODO - FIX THIS.  need a general strategy for only updating
            # if there's a "pause" in the action.
            op.tubes.append(op_tube)
    
    ## i'd love to cache this, but it screws up the coloring stuff  :-/
    def _get_tubes_counter(self):
        return Counter(self.tubes)


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

class ExperimentDialogHandler(Controller):

    # keep around a ref to the underlying widget so we can add columns dynamically
    table_editor = Instance(TableEditorQt)
    
#     def init_info(self, info):
#         
#         # set the parent model object for any preexisting tubes
#         for tube in self.model.tubes:
#             tube._parent = self.model
#             
#         Controller.init_info(self, info)
    
    def closed(self, info, is_ok):
        for tube in self.model.tubes:
            tube.on_trait_change(self._try_multiedit, '+', remove = True)
        
    def _on_delete_column(self, obj, column, info):
        # TODO - be able to remove traits.....
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
            fcs = FCMeasurement(ID='new tube', datafile = path)
            
            if len(self.model.tubes) > 0: 
                # easier than making all the dynamic traits anew
                tube = self.model.tubes[0].clone_traits(copy = "shallow")
                tube.reset_traits(traits = tube.copyable_trait_names())
            else:
                tube = Tube()
                
            tube.trait_set(Name = fcs.meta['$SRC'],
                           _file = path,
                           _parent = self.model)
            
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
            
            if len(self.model.tubes) > 0: 
                # easier than making all the dynamic traits anew
                tube = self.model.tubes[0].clone_traits(copy = "shallow")
                tube.reset_traits(traits = tube.copyable_trait_names())
            else:
                tube = Tube()
            
            tube.trait_set(_file = well_data.datafile,
                           Row = well_data.position['new plate'][0],
                           Col = well_data.position['new plate'][1],
                           Name = well_data.meta['$SRC'],
                           _parent = self.model)

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
        
    def _add_metadata(self, name, label, trait):
        """
        Add a new tube metadata
        """
        
        trait_names = self.model.tubes[0].trait_names(transient = not_true)
            
        if not name in trait_names:
            for tube in self.model.tubes:
                tube.add_trait(name, trait)
                tube.on_trait_change(self._try_multiedit, name)    

            self.table_editor.columns.append(ExperimentColumn(name = name,
                                                              label = label))
                
    def _remove_metadata(self, meta_name, column_name, meta_type):
        # TODO - make it possible to remove metadata
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
            
            trait_names = self.model.tubes[0].trait_names(transient = not_true)
            for trait_name in trait_names:
                if trait_name == "Name":  # already have a "Name" column
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
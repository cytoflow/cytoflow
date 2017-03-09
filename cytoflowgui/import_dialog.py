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
Created on Feb 26, 2015

@author: brian
"""

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"
    
from collections import OrderedDict
    
from traits.api import (HasTraits, HasStrictTraits, provides, Instance, Str, 
                        Int, List, Bool, Enum, Float, DelegatesTo,
                        Property, BaseCStr, on_trait_change, Dict, cached_property)
                       
from traitsui.api import UI, Group, View, Item, TableEditor, OKCancelButtons, \
                         Controller

from traitsui.qt4.table_editor import TableEditor as TableEditorQt

from pyface.i_dialog import IDialog
from pyface.api import Dialog, FileDialog, error, OK, confirm

from pyface.qt import QtCore, QtGui
from pyface.constant import OK as PyfaceOK

from pyface.ui.qt4.directory_dialog import DirectoryDialog as QtDirectoryDialog

from traitsui.table_column import ObjectColumn

from cytoflow import Tube as CytoflowTube
from cytoflow import Experiment, ImportOp
from cytoflow.operations.import_op import check_tube
import cytoflow.utility as util

import fcsparser

def not_true ( value ):
    return (value is not True)

def not_false ( value ):
    return (value is not False)

class Tube(HasTraits):
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
    "is an experimental condition" (everything but file, source, tube, row, 
    column, parent).
    
    We also use the "transient" flag to specify traits that shouldn't be 
    displayed in the editor.  This matches well with the traits that
    every HasTraits-derived class has by default (all of which are transient.)
    """
    
    # these are the traits that every tube has.  every other trait is
    # dynamically created. 
    
    # the file name.
    file = Str(transient = True)
    
    # need a link to the model; needed for row coloring
    parent = Instance("ExperimentDialogModel", transient = True)
    
    # needed for fast hashing
    conditions = Dict
    
    all_conditions_set = Property(Bool, depends_on = "conditions")
            
    def conditions_hash(self):
        ret = int(0)
    
        for key, value in self.conditions.iteritems():
            if not ret:
                ret = hash((key, value))
            else:
                ret = ret ^ hash((key, value))
                
        return ret
    
    def _anytrait_changed(self, name, old, new):
        if self.trait(name).condition:
            old_hash = self.conditions_hash()
            
            self.parent.counter[old_hash] -= 1
            if self.parent.counter[old_hash] == 0:
                del self.parent.counter[old_hash]
                
            self.conditions[name] = new
            
            new_hash = self.conditions_hash()
            if new_hash not in self.parent.counter:
                self.parent.counter[new_hash] = 1
            else:
                self.parent.counter[new_hash] += 1
                
    @cached_property
    def _get_all_conditions_set(self):
        return len(filter(lambda x: x is None or x == "", self.conditions.values())) == 0

    
class ExperimentColumn(ObjectColumn):
    # override ObjectColumn.get_cell_color
    def get_cell_color(self, obj):
        if obj.parent.is_tube_unique(obj) and obj.all_conditions_set:
            return super(ObjectColumn, self).get_cell_color(object)
        else:
            return QtGui.QColor('lightpink')
        
    # override the context menu
#     def get_menu(self, obj):
#         return Menu(Action(name = "Remove Tubes",
#                            action = "_on_remove_tubes"),
#                     Action(name = "Remove Column",
#                            action = "_on_remove_column"))
                
    
class ExperimentDialogModel(HasStrictTraits):
    """
    The model for the Experiment setup dialog.
    """
        
    # the heart of the model, a list of Tubes
    tubes = List(Tube)
    
    # keeps track of whether a tube is unique or not
    counter = Dict(Int, Int)
    
    # are all the tubes unique and filled?
    valid = Property()
    
    # a dummy Experiment, with the first Tube and no events, so we can check
    # subsequent tubes for voltage etc. and fail early.
    dummy_experiment = Instance(Experiment)
    
    # a dict of the dynamic TraitTypes added to the tube instances
    tube_traits = Instance(OrderedDict, ())    

    # traits to communicate with the TabularEditor
    update = Bool
    refresh = Bool
    selected = List()
    
    view = View(
            Group(
                Item(name = 'tubes', 
                     id = 'table', 
                     editor = TableEditor(editable = True,
                                          sortable = True,
                                          auto_size = True,
                                          configurable = False,
                                          selection_mode = 'cells',
                                          selected = 'selected'),
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
                          "bool" : Bool,
                          "int" : Int}
        
        new_tubes = []
        for op_tube in op.tubes:
            tube = Tube(file = op_tube.file,
                        parent = self)
            
            # first load the tube's metadata and set special columns
            try:
                tube_meta = fcsparser.parse(op_tube.file, 
                                            meta_data_only = True, 
                                            reformat_meta = True)
                #tube_channels = tube_meta["_channels_"].set_index("$PnN")
            except Exception as e:
                error(None, "FCS reader threw an error on tube {0}: {1}"\
                            .format(op_tube.file, e.value),
                      "Error reading FCS file")
                return
            
            # if we're the first tube loaded, create a dummy experiment
            if not self.dummy_experiment:
                self.dummy_experiment = ImportOp(tubes = [op_tube],
                                                 conditions = op.conditions,
                                                 coarse_events = 1).apply()
                
            if '$SRC' in tube_meta:    
                self.tube_traits["$SRC"] = Str(condition = False)
                tube.add_trait("$SRC", Str(condition = False))
                tube.trait_set(**{"$SRC" : tube_meta['$SRC']})
                
            if 'TUBE NAME' in tube_meta:
                self.tube_traits["TUBE NAME"] = Str(condition = False)
                tube.add_trait("TUBE NAME", Str(condition = False))
                tube.trait_set(**{"TUBE NAME" : tube_meta['TUBE NAME']})
                
            if '$SMNO' in tube_meta:
                self.tube_traits["$SMNO"] = Str(condition = False)
                tube.add_trait("$SMNO", Str(condition = False))
                tube.trait_set(**{"$SMNO" : tube_meta['SMNO']})
                
            if 'WELL ID' in tube_meta:                
                pos = tube_meta['WELL ID']
                row = pos[0]
                col = int(pos[1:3])
                
                self.tube_traits["Row"] = Str(condition = False)
                self.tube_traits["Col"] = Int(condition = False)
                tube.add_trait("Row", Str(condition = False))
                tube.add_trait("Col", Int(condition = False))
                tube.trait_set(**{"Row" : row, "Col" : col})

            # next set conditions
            try:
                conditions_list = op_tube.conditions_list
            except:
                conditions_list = op_tube.conditions.keys()
                
            for condition in conditions_list:
                condition_dtype = op.conditions[condition]
                condition_trait = \
                    dtype_to_trait[condition_dtype](condition = True)
                tube.add_trait(condition, condition_trait)
                if not condition in self.tube_traits:
                    self.tube_traits[condition] = condition_trait
            tube.trait_set(**op_tube.conditions)
            
            new_tubes.append(tube)
            
        self.tubes.extend(new_tubes)
    
    @on_trait_change('tubes_items')
    def _tubes_items(self, event):
        for tube in event.added:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1
                
        for tube in event.removed:
            tube_hash = tube.conditions_hash()
            if self.counter[tube_hash] == 1:
                del self.counter[tube_hash]
            else:
                self.counter[tube_hash] -= 1

    
    def update_import_op(self, op):
        trait_to_dtype = {"Str" : "category",
                          "Float" : "float",
                          "Bool" : "bool",
                          "Int" : "int"}
        
        conditions = {}
        for trait_name, trait in self.tube_traits.items():
            if not trait.condition:
                continue

            trait_type = trait.__class__.__name__
            conditions[trait_name] = trait_to_dtype[trait_type]
            
        tubes = []
        for tube in self.tubes:
            op_tube = CytoflowTube(file = tube.file,
                                   conditions = tube.trait_get(condition = True),
                                   conditions_list = [x for x in self.tube_traits.keys() if self.tube_traits[x].condition])
            tubes.append(op_tube)
            
        op.conditions = conditions
        op.tubes = tubes
            
    def is_tube_unique(self, tube):
        tube_hash = tube.conditions_hash()
        if tube_hash in self.counter:
            return self.counter[tube.conditions_hash()] == 1
        else:
            return False
    
    
    def _get_valid(self):
        return len(set(self.counter)) == len(self.tubes) and all([x.all_conditions_set for x in self.tubes])
   

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

    # keep a ref to the table editor so we can add columns dynamically
    table_editor = Instance(TableEditorQt)

    # keep a refs to enable/disable.
    btn_add_cond = Instance(QtGui.QPushButton)
    btn_remove_cond = Instance(QtGui.QPushButton)
    btn_remove_tubes = Instance(QtGui.QPushButton)
    
    updating = Bool(False)
    
    def init(self, info):
        """ Overrides Handler.init() """
        
        self.table_editor = info.ui.get_editors('tubes')[0]
        
        if self.model.tube_traits:
            trait_to_col = {"Str" : " (Category)",
                            "Float" : " (Number)",
                            "Bool" : " (T/F)",
                            "Int" : " (Int)"}
            
            for name, trait in self.model.tube_traits.iteritems():
                trait_type = trait.__class__.__name__
                label = name + trait_to_col[trait_type] \
                        if trait.condition \
                        else name
                self.table_editor.columns.append(ExperimentColumn(name = name,
                                                 label = label,
                                                 editable = trait.condition))
                
        return True
    
    def closed(self, info, is_ok):
        for trait_name, trait in self.model.tube_traits.items():
            if not trait.condition:
                continue
            for tube in self.model.tubes:
                tube.on_trait_change(self._try_multiedit, 
                                     trait_name, 
                                     remove = True)

        
    def _on_add_condition(self):
        """
        Add a new condition.  Use TraitsUI to make a simple dialog box.
        """
        
        class ValidPythonIdentifier(BaseCStr):
    
            info_text = 'a valid python identifier'
    
            def validate(self, obj, name, value):
                value = super(ValidPythonIdentifier, self).validate(obj, name, value)
                if util.sanitize_identifier(value) == value:
                    return value 
                
                self.error(obj, name, value)
        
        class NewTrait(HasTraits):    
            condition_name = ValidPythonIdentifier()
            condition_type = Enum(["Category", "Number", "True/False"])
    
            view = View(Item(name = 'condition_name'),
                        Item(name = 'condition_type'),
                        buttons = OKCancelButtons,
                        title = "Add a condition",
                        close_result = False)
            
            def _validate_condition_name(self, x):
                return util.sanitize_identifier(x)
            
        
        new_trait = NewTrait()
        new_trait.edit_traits(kind = 'modal')
        
        if not new_trait.condition_name: 
            return

        name = new_trait.condition_name
        
        if name in self.model.dummy_experiment.channels:
            error(None, 
                  "Condition \"{0}\" conflicts with a channel name.".format(name),
                  "Error adding condition")
            return
        
        if name in self.model.tube_traits:
            error(None,
                  "The experiment already has a condition named \"{0}\".".format(name),
                  "Error adding condition")
            return
        
        if new_trait.condition_type == "Category":
            self._add_metadata(name, name + " (Category)", Str(condition = True))
        elif new_trait.condition_type == "Number":
            self._add_metadata(name, name + " (Number)", Float(condition = True))
        else:
            self._add_metadata(name, name + " (T/F)", Bool(condition = True))       
        
    def _on_remove_condition(self):
        pass
        col = self.model.selected[0][1]
        if self.model.tubes[0].trait(col).condition == True:
            conf = confirm(None,
                           "Are you sure you want to remove condition \"{}\"?".format(col),
                           "Remove condition?")
            if conf:
                self._remove_metadata(col)
        else:
            error(None, 
                  "Can't remove column {}".format(col),
                  "Error")

        
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
        
        new_tubes = []
        for path in file_dialog.paths:
            try:
                tube_meta = fcsparser.parse(path, 
                                            meta_data_only = True, 
                                            reformat_meta = True)
                #tube_channels = tube_meta["_channels_"].set_index("$PnN")
            except Exception as e:
                raise RuntimeError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(path, e.value))
                
                
            # if we're the first tube loaded, create a dummy experiment
            if not self.model.dummy_experiment:
                self.model.dummy_experiment = ImportOp(tubes = [CytoflowTube(file = path)],
                                                       coarse_events = 1).apply()
                                                       
            # check the next tube against the dummy experiment
            try:
                check_tube(path, self.model.dummy_experiment)
            except util.CytoflowError as e:
                error(None, e.__str__(), "Error importing tube")
                return
                
            tube = Tube()
            
            for trait_name, trait in self.model.tube_traits.items():
                tube.add_trait(trait_name, trait)
                
                # this magic makes sure the trait is actually defined
                # in tube.__dict__, so it shows up in trait_names etc.
                tube.trait_set(**{trait_name : trait.default_value})
                if trait.condition:
                    tube.on_trait_change(self._try_multiedit, trait_name)
            
            tube.trait_set(file = path, parent = self.model)
            
            if '$SRC' in tube_meta:    
                self._add_metadata("$SRC", "$SRC", Str(condition = False))
                tube.trait_set(**{"$SRC" : tube_meta['$SRC']})
                
            if 'TUBE NAME' in tube_meta:
                self._add_metadata("TUBE NAME", "TUBE NAME", Str(condition = False))
                tube.trait_set(**{"TUBE NAME" : tube_meta['TUBE NAME']})
                
            if '$SMNO' in tube_meta:
                self._add_metadata("$SMNO", "$SMNO", Str(condition = False))
                tube.trait_set(**{"$SMNO" : tube_meta['$SMNO']})
                
            if 'WELL ID' in tube_meta:
                self._add_metadata("Row", "Row", Str(condition = False))
                self._add_metadata("Col", "Col", Int(condition = False))
                
                pos = tube_meta['WELL ID']
                row = pos[0]
                col = int(pos[1:3])
                
                tube.trait_set(**{"Row" : row, "Col" : col})
                
            new_tubes.append(tube)

        self.model.tubes.extend(new_tubes)
            
    def _on_remove_tubes(self):
        conf = confirm(None,
                       "Are you sure you want to remove the selected tube(s)?",
                       "Remove tubes?")
        if conf:
            for (tube, _) in self.model.selected:
                self.model.tubes.remove(tube)
                
        if not self.model.tubes:
            self.model.dummy_experiment = None

    
    @on_trait_change('model.tubes_items', post_init = True)
    def _tubes_count(self):
        if self.btn_add_cond:
            if len(self.model.tubes) == 0:
                self.btn_add_cond.setEnabled(False)
                self.btn_remove_cond.setEnabled(False)
                self.btn_remove_tubes.setEnabled(False)
            else:
                self.btn_add_cond.setEnabled(True)
                self.btn_remove_cond.setEnabled(True)
                self.btn_remove_tubes.setEnabled(True)

    

        
#     def _on_remove_tubes(self, info, selection):
#         for (tube, _) in info.ui.context['object'].selected:
#             self.model.tubes.remove(tube)
#                 
#                 
#     def _on_remove_column(self, info, selection):         
#         col = info.ui.context['object'].selected[0][1]
#         if self.model.tubes[0].trait(col).condition == True:
#             self._remove_metadata(col)
#         else:
#             error(None, "Can't remove column {}".format(col), "Error")
            
    def _try_multiedit(self, obj, name, old, new):
        """
        See if there are multiple elements selected when a tube's trait changes
        
        and if so, edit the same trait for all the selected tubes.
        """
        
        if self.updating:
            return
        
        self.updating = True

        for tube, trait_name in self.model.selected:
            if tube != obj:

                old_hash = tube.conditions_hash()
                self.model.counter[old_hash] -= 1
                if self.model.counter[old_hash] == 0:
                    del self.model.counter[old_hash]            
    
                # update the underlying traits without notifying the editor
                tube.trait_setq(**{trait_name: new})
                tube.conditions[trait_name] = new
                
                new_hash = tube.conditions_hash()
                if new_hash not in self.model.counter:
                    self.model.counter[new_hash] = 1
                else:
                    self.model.counter[new_hash] += 1
                

        # now refresh the editor all at once
        self.table_editor.refresh_editor()
        self.updating = False
        
    def _add_metadata(self, name, label, trait):
        """
        Add a new tube metadata
        """
        
        if trait.condition:
            self.model.counter.clear()
            
        trait_names = self.model.tube_traits.keys()
            
        if not name in trait_names:
            self.model.tube_traits[name] = trait
            
            for tube in self.model.tubes:
                tube.add_trait(name, trait)
                
                # this magic makes sure the trait is actually defined
                # in tube.__dict__, so it shows up in trait_names etc.
                tube.trait_set(**{name : trait.default_value})
                tube.conditions[name] = trait.default_value
                if trait.condition:
                    tube.on_trait_change(self._try_multiedit, name)
                    
                    tube_hash = tube.conditions_hash()
                    if tube_hash in self.model.counter:
                        self.model.counter[tube_hash] += 1
                    else:
                        self.model.counter[tube_hash] = 1
                

            self.table_editor.columns.append(ExperimentColumn(name = name,
                                                              label = label,
                                                              editable = trait.condition))
            
    def _remove_metadata(self, name):
        self.model.counter.clear()
        
        if name in self.model.tube_traits:
            del self.model.tube_traits[name]
             
            for tube in self.model.tubes:
                if tube.trait(name).condition:
                    tube.on_trait_change(self._try_multiedit, name, remove = True)
                    
                tube.remove_trait(name)
                del tube.conditions[name]
                
                tube_hash = tube.conditions_hash()
                if tube_hash in self.model.counter:
                    self.model.counter[tube_hash] += 1
                else:
                    self.model.counter[tube_hash] = 1   
                
        table_column = next((x for x in self.table_editor.columns if x.name == name))
        self.table_editor.columns.remove(table_column)
        

        
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

    handler = Instance(ExperimentDialogHandler)
    model = DelegatesTo('handler')

    ui = Instance(UI)
    
    def __init__(self, **kwargs):
        super(ExperimentDialog, self).__init__(**kwargs)
        self.handler = ExperimentDialogHandler()
        self.model = ExperimentDialogModel()
        
    def open(self):
        super(ExperimentDialog, self).open()
        
        if self.return_code == OK and not self.model.valid:
            error(None, "Invalid experiment setup.\n"
                        "Was each tube's metadata unique?",
                        "Invalid experiment!")
            self.open()
            
        return self.return_code
        

    def _create_buttons(self, parent):
        """ 
        Create the buttons at the bottom of the dialog box.
        
        We're overriding (and stealing code from) pyface.qt._create_buttons in
        order to add "Add tube.... " and "Add plate..." buttons.
        """
         
        buttons = QtGui.QWidget()
        #layout = QtGui.QHBoxLayout()
        layout = QtGui.QGridLayout()
        
        btn_add_tube = QtGui.QPushButton("Add tubes...")
        layout.addWidget(btn_add_tube, 0, 0)
        QtCore.QObject.connect(btn_add_tube, QtCore.SIGNAL('clicked()'),
                               self.handler._on_add_tubes)
        
        btn_remove_tubes = QtGui.QPushButton("Remove tubes")
        layout.addWidget(btn_remove_tubes, 1, 0)
        QtCore.QObject.connect(btn_remove_tubes, QtCore.SIGNAL('clicked()'),
                               self.handler._on_remove_tubes)
        btn_remove_tubes.setEnabled(len(self.model.tubes) > 0)
        self.handler.btn_remove_tubes = btn_remove_tubes

        
        # start disabled if there aren't any tubes in the model
        btn_add_cond = QtGui.QPushButton("Add condition...")
        layout.addWidget(btn_add_cond, 0, 1)
        QtCore.QObject.connect(btn_add_cond, QtCore.SIGNAL('clicked()'),
                               self.handler._on_add_condition)
        btn_add_cond.setEnabled(len(self.model.tubes) > 0)
        self.handler.btn_add_cond = btn_add_cond
        
        btn_remove_cond = QtGui.QPushButton("Remove condition")
        layout.addWidget(btn_remove_cond, 1, 1)
        QtCore.QObject.connect(btn_remove_cond, QtCore.SIGNAL('clicked()'),
                               self.handler._on_remove_condition)
        btn_remove_cond.setEnabled(len(self.model.tubes) > 0)
        self.handler.btn_remove_cond = btn_remove_cond
        
        layout.addItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Maximum), 0, 2)
        layout.addItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Maximum), 1, 2)
        
        #layout.addStretch()

        # 'OK' button.
        btn_ok = QtGui.QPushButton("OK")
        btn_ok.setDefault(True)
        layout.addWidget(btn_ok, 0, 3)
        QtCore.QObject.connect(btn_ok, QtCore.SIGNAL('clicked()'),
                               self.control, QtCore.SLOT('accept()'))
        
        # 'Cancel' button.
        btn_cancel = QtGui.QPushButton("Cancel")
        layout.addWidget(btn_cancel, 0, 4)
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
    
    d = ExperimentDialog()
    d.size = (550, 500)
    d.open()
    
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
Created on Feb 26, 2015

@author: brian
"""

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"
    
from pathlib import Path
        
from traits.api import (HasTraits, HasStrictTraits, provides, Instance, Str, 
                        Int, List, Bool, Enum, Float, DelegatesTo, TraitType,
                        Property, BaseCStr, CStr, on_trait_change, Dict, Event,
                        cached_property)
                       
from traitsui.api import (UI, Group, View, Item, TableEditor, OKCancelButtons,
                          Controller, CheckListEditor, TextEditor, BooleanEditor,
                          InstanceEditor, ListStrEditor, HGroup, ButtonEditor)

from traitsui.menu import OKButton

from traitsui.qt4.table_editor import TableEditor as TableEditorQt

from pyface.i_dialog import IDialog
from pyface.api import Dialog, FileDialog, error, warning, OK, confirm, YES

from pyface.qt import QtCore, QtGui
from pyface.constant import OK as PyfaceOK

from traitsui.table_column import ObjectColumn, TableColumn

from cytoflow import Tube as CytoflowTube
from cytoflow import Experiment, ImportOp
from cytoflow.operations.import_op import check_tube, parse_tube
import cytoflow.utility as util

from cytoflowgui.vertical_list_editor import VerticalListEditor

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
    serialization (dynamic traits don't survive pickling when sending tubes to 
    the remote process)  (well, their values do, but neither the trait type nor 
    the metadata do.)
    
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
    
    # metadata from the FCS file
    meta = Dict
    
    all_conditions_set = Property(Bool, depends_on = "conditions")
            
    def conditions_hash(self):
        ret = int(0)
    
        for key, value in self.conditions.items():
            if not ret:
                ret = hash((key, value))
            else:
                ret = ret ^ hash((key, value))
                
        return ret
    
    def _anytrait_changed(self, name, old, new):
        if self.parent is not None and name in self.parent.tube_traits_dict and self.parent.tube_traits_dict[name].trait_type != "Read Only":
            old_hash = self.conditions_hash()
            self.conditions[name] = new
            new_hash = self.conditions_hash()
            
            if old_hash in self.parent.counter:
                self.parent.counter[old_hash] -= 1
                
                if self.parent.counter[old_hash] == 0:
                    del self.parent.counter[old_hash]
                
            
                if new_hash not in self.parent.counter:
                    self.parent.counter[new_hash] = 1
                else:
                    self.parent.counter[new_hash] += 1
                
    @cached_property
    def _get_all_conditions_set(self):
        return len([x for x in list(self.conditions.values()) if x is None or x == ""]) == 0
    
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
    
# class ValidPythonIdentifier(BaseCStr):
# 
#     info_text = 'a valid python identifier'
# 
#     def validate(self, obj, name, value):
#         value = super(ValidPythonIdentifier, self).validate(obj, name, value)
#         if util.sanitize_identifier(value) == value:
#             return value 
#          
#         self.error(obj, name, value)
    
class TubeTrait(HasStrictTraits):
    model = Instance('ExperimentDialogModel')
    trait = Property
    name = CStr
    trait_type = Enum(['Read Only', 'Category', 'Number', 'True/False'])
    remove_trait = Event
    editable = Property
    
    default_view = View(HGroup(Item('name'), 
                               Item('trait_type'), 
                               Item('remove_trait',
                                    editor = ButtonEditor(label = 'X'))))
    
    # magic - gets values for the `trait` property
    def _get_trait(self):
        if self.trait_type == 'Read Only' or self.trait_type == 'Category':
            return Str()
        elif self.trait_type == 'Number':
            return Float()
        elif self.trait_type == 'True/False':
            return Bool()
    
    def _get_editable(self):
        return self.trait_type != 'Read Only' and self.name not in self.model.fcs_metadata
    
    @on_trait_change('remove_trait')
    def _remove_trait(self):
        self.model.tube_traits.remove(self)
    
class ExperimentDialogModel(HasStrictTraits):
    """
    The model for the Experiment setup dialog.
    """
        
    # t list of Tubes (rows in the table)
    tubes = List(Tube)

    # a list of the traits that have been added to Tube instances
    # (columns in the table)
    tube_traits = List(TubeTrait)
    tube_traits_dict = Dict
    
    # keeps track of whether a tube is unique or not
    counter = Dict(Int, Int)
    
    # are all the tubes unique and filled?
    valid = Property(List)
    
    # a dummy Experiment, with the first Tube and no events, so we can check
    # subsequent tubes for voltage etc. and fail early.
    dummy_experiment = Instance(Experiment)

    # traits to communicate with the TabularEditor
    update = Bool
    refresh = Bool
    selected = List()
    
    # traits to communicate with the traits_view
    fcs_metadata = Property
    selected_fcs_metadata = Str
    add_fcs_metadata = Event    
    
    default_view = View(
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
    
    traits_view = View(HGroup(
        Item('fcs_metadata',
             editor = ListStrEditor(selected = 'selected_fcs_metadata',
                                    editable = False)),
        Item('add_fcs_metadata',
             editor = ButtonEditor(label = '->')),
        Item('tube_traits',
             editor = VerticalListEditor(
                 editor = InstanceEditor(),
                 style = 'custom',
                 mutable = False))),
        buttons = [OKButton])
    
#     def control_traits_view(self):
#         return View(HGroup(Item('channel',
#                                 editor = EnumEditor(name = 'handler.context.previous_wi.channels')),
#                            Item('file',
#                                 show_label = False)),
#                     handler = self)
    
    def init_model(self, op, conditions, metadata):
#         
#         dtype_to_trait = {"category" : Str,
#                           "float" : Float,
#                           "bool" : Bool,
#                           "int" : Int}
#         
# #          
#         tube_meta = list(metadata['fcs_metadata'].values())[0] \
#                     if 'fcs_metadata' in metadata else {}
#         
        
        if 'CF_File' not in conditions:
            self.tube_traits.append(TubeTrait(model = self,
                                              name = 'CF_File',
                                              trait_type = 'Read Only'))
            
        for name, condition in conditions.items():
            if str(condition.dtype).startswith("category") or str(condition.dtype).startswith('object'):
                trait_type = 'Category'
            elif str(condition.dtype).startswith("int") or str(condition.dtype).startswith("float"):
                trait_type = 'Number'
            elif str(condition.dtype) == "bool":
                trait_type = 'True/False'
                
            self.tube_traits.append(TubeTrait(model = self,
                                              name = name,
                                              trait_type = trait_type))
            
#             self.tube_traits.append(Str(name = 'CF_File', condition = False))
# 
#         for name, condition in conditions.items():
#             if str(condition.dtype).startswith("category") or str(condition.dtype).startswith('object'):
#                 self.tube_traits.append(Str(name = name, condition = True))
#             elif str(condition.dtype).startswith("int"):
#                 self.tube_traits.append(Int(name = name, condition = True))
#             elif str(condition.dtype).startswith("float"):
#                 self.tube_traits.append(Float(name = name, condition = True))
#             elif str(condition.dtype) == "bool":
#                 self.tube_traits.append(Bool(name = name, condition = True))
                
#         new_tubes = []
        self.dummy_experiment = None
        
        shown_error = False
        
#         if '$SRC' in tube_meta:
#             self.show_fcs_metadata.append('$SRC')
#             
#         if 'TUBE NAME' in tube_meta:
#             self.show_fcs_metadata.append('TUBE NAME')
#             
#         if '$SMNO' in tube_meta:
#             self.show_fcs_metadata.append('$SMNO')
#             
#         if 'CF_Row' in tube_meta:
#             self.show_fcs_metadata.append('CF_Row')
#             
#         if 'CF_Col' in tube_meta:
#             self.show_fcs_metadata.append('CF_Col')

#         for meta in tube_meta.keys():
#             if meta.startswith('CF_'):
#                 self.show_fcs_metadata.append(meta)
        
        for op_tube in op.tubes:
            tube = Tube(file = op_tube.file,
                        parent = self,
                        meta = metadata['fcs_metadata'][op_tube.file])
            
            try:
                fcsparser.parse(op_tube.file, meta_data_only = True)
            except Exception:
                if not shown_error:
                    warning(None,
                            "Had trouble loading some of the experiment's FCS "
                            "files.  You will need to re-add them.")
                    shown_error = True
                continue
            
            # if we're the first tube loaded, create a dummy experiment
            # and setup default metadata columns
            if not self.dummy_experiment:
                self.dummy_experiment = ImportOp(tubes = [op_tube],
                                                 conditions = op.conditions,
                                                 events = 1).apply()
                                                 
            self.tubes.append(tube)  # adds the dynamic traits to the tube
            
            tube.trait_set(**op_tube.conditions)

                    
            # set up metadata for tube
#             for meta in self.show_fcs_metadata:
#                 if meta not in self.tube_traits:
# #                     self.tube_traits[meta] = Str(condition = False)
#                     tube.add_trait(meta, Str(condition = False))
#                     tube.trait_set(**{meta : tube_meta[meta]})
                    
#                 self.tube_traits["$SRC"] = Str(condition = False)
#                 tube.add_trait("$SRC", Str(condition = False))
#                 tube.trait_set(**{"$SRC" : tube_meta['$SRC']})
#                 
#             if 'TUBE NAME' in tube_meta:
#                 self.tube_traits["TUBE NAME"] = Str(condition = False)
#                 tube.add_trait("TUBE NAME", Str(condition = False))
#                 tube.trait_set(**{"TUBE NAME" : tube_meta['TUBE NAME']})
#                 
#             if '$SMNO' in tube_meta:
#                 self.tube_traits["$SMNO"] = Str(condition = False)
#                 tube.add_trait("$SMNO", Str(condition = False))
#                 tube.trait_set(**{"$SMNO" : tube_meta['$SMNO']})
#                 
#             if 'WELL ID' in tube_meta:                
#                 pos = tube_meta['WELL ID']
#                 row = pos[0]
#                 col = int(pos[1:3])
#                 
#                 self.tube_traits["Row"] = Str(condition = False)
#                 self.tube_traits["Col"] = Int(condition = False)
#                 tube.add_trait("Row", Str(condition = False))
#                 tube.add_trait("Col", Int(condition = False))
#                 tube.trait_set(**{"Row" : row, "Col" : col})

            # set the filename 
            
#             if 'CF_File' not in op_tube.conditions.keys():
#                 tube.add_trait('CF_File', Str(name = 'CF_File'))
#                 tube.trait_set(**{'CF_File' : Path(op_tube.file).stem})
#                 
#             # next set conditions
#                 
#             for condition in op_tube.conditions.keys():
#                 condition_dtype = op.conditions[condition]
#                 condition_trait = \
#                     dtype_to_trait[condition_dtype](name = condition, condition = True)
#                 tube.add_trait(condition, condition_trait)
#                 tube.conditions[condition] = op_tube.conditions[condition]
#                 
#                 if len(list(filter(lambda x: x.name == condition, self.tube_traits))) == 0:
#                     self.tube_traits.append(condition_trait)


#             tube.trait_set(**op_tube.conditions)
            
#             new_tubes.append(tube)
#             tube.append()
            
#         self.tubes.append(new_tubes)
    
    
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
                
    @on_trait_change('tube_traits_items')
    def _tube_traits_items(self, event):
        for trait in event.added:
            self.tube_traits_dict[trait.name] = trait
            
        for trait in event.removed:
            del self.tube_traits_dict[trait.name]
                
    
    def update_import_op(self, op):
        trait_to_dtype = {"Str" : "category",
                          "Float" : "float",
                          "Bool" : "bool",
                          "Int" : "int"}
        
        conditions = {}
        for trait_name, trait in self.tube_traits:
            if not trait.condition:
                continue

            trait_type = trait.__class__.__name__
            conditions[trait_name] = trait_to_dtype[trait_type]
            
        tubes = []
        for tube in self.tubes:
            op_tube = CytoflowTube(file = tube.file,
                                   conditions = tube.trait_get(condition = True))
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
    
    # magic: gets the list of FCS metadata for the trait list editor
    def _get_fcs_metadata(self):
        return ['$BTIM', '$DATE', '$FIL']

class ExperimentDialogHandler(Controller):

    # keep a ref to the table editor so we can add columns dynamically
    table_editor = Instance(TableEditorQt)

    # keep a refs to enable/disable.
    btn_remove_tubes = Instance(QtGui.QPushButton)
    btn_metadata = Instance(QtGui.QPushButton)
    
    updating = Bool(False)
    
    def init(self, info):
        """ Overrides Handler.init() """
        
        # save a reference to the table editor
        self.table_editor = info.ui.get_editors('tubes')[0]
        
        for trait in self.model.tube_traits:
            self.table_editor.columns.append(ExperimentColumn(name = trait.name,
                                                              editable = trait.editable))
#         
#         if self.model.tube_traits:
#             trait_to_col = {"Str" : " (Category)",
#                             "Float" : " (Number)",
#                             "Bool" : " (T/F)",
#                             "Int" : " (Int)"}
#             
#             for trait in self.model.tube_traits:
#                 trait_type = trait.__class__.__name__
#                 label = trait.name + trait_to_col[trait_type] \
#                         if trait.condition \
#                         else trait.name
#                 self.table_editor.columns.append(ExperimentColumn(name = trait.name,
#                                                  label = label,
#                                                  editable = trait.condition))
                
        return True
    
    def closed(self, info, is_ok):
        for trait in self.model.tube_traits:
            if not trait.condition:
                continue
            for tube in self.model.tubes:
                tube.on_trait_change(self._try_multiedit, 
                                     trait.name, 
                                     remove = True)
        
#     def _on_add_condition(self):
#         """
#         Add a new condition.  Use TraitsUI to make a simple dialog box.
#         """
#         
#         class ValidPythonIdentifier(BaseCStr):
#     
#             info_text = 'a valid python identifier'
#     
#             def validate(self, obj, name, value):
#                 value = super(ValidPythonIdentifier, self).validate(obj, name, value)
#                 if util.sanitize_identifier(value) == value:
#                     return value 
#                 
#                 self.error(obj, name, value)
#         
#         class NewTrait(HasTraits):    
#             condition_name = ValidPythonIdentifier()
#             condition_type = Enum(["Category", "Number", "True/False"])
#     
#             view = View(Item(name = 'condition_name'),
#                         Item(name = 'condition_type'),
#                         buttons = OKCancelButtons,
#                         title = "Add a condition",
#                         close_result = False)
#             
#             def _validate_condition_name(self, x):
#                 return util.sanitize_identifier(x)
#             
#         
#         new_trait = NewTrait()
#         new_trait.edit_traits(kind = 'modal')
#         
#         if not new_trait.condition_name: 
#             return
# 
#         name = new_trait.condition_name
#         
#         if name in self.model.dummy_experiment.channels:
#             error(None, 
#                   "Condition \"{0}\" conflicts with a channel name.".format(name),
#                   "Error adding condition")
#             return
#         
#         if name in self.model.tube_traits:
#             error(None,
#                   "The experiment already has a condition named \"{0}\".".format(name),
#                   "Error adding condition")
#             return
#         
#         if new_trait.condition_type == "Category":
#             self._add_metadata(name, name + " (Category)", Str(condition = True))
#         elif new_trait.condition_type == "Number":
#             self._add_metadata(name, name + " (Number)", Float(condition = True))
#         else:
#             self._add_metadata(name, name + " (T/F)", Bool(condition = True))       
#         
#     def _on_remove_condition(self):
#         col = self.model.selected[0][1]
#         if self.model.tubes[0].trait(col).condition == True:
#             conf = confirm(None,
#                            "Are you sure you want to remove condition \"{}\"?".format(col),
#                            "Remove condition?")
#             if conf == YES:
#                 self._remove_metadata(col)
#         else:
#             error(None, 
#                   "Can't remove column {}".format(col),
#                   "Error")
            
    def _on_edit_metadata(self):
#         pass
        self.model.edit_traits('traits_view', kind = 'livemodal')
    
    def _on_import(self):
        """
        Import format: CSV, first column is filename, path relative to CSV.
        others are conditions, type is autodetected.  first row is header
        with names.
        """
        pass

        
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
            try:
                fcsparser.parse(path, 
                                meta_data_only = True)
            except Exception as e:
                raise RuntimeError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(path, e.value))
                
                
            # if we're the first tube loaded, create a dummy experiment
            # and setup default metadata columns
            if not self.model.dummy_experiment:
                self.model.dummy_experiment = ImportOp(tubes = [CytoflowTube(file = path)],
                                                       events = 1).apply()
#                                                        
#                 tube_meta = self.model.dummy_experiment.metadata['fcs_metadata'][path]
#                 self.model.fcs_metadata = sorted(list(tube_meta.keys()))
#                                                                        
#                 if '$SRC' in tube_meta and '$SRC' not in self.model.show_fcs_metadata:
#                     self.model.show_fcs_metadata.append('$SRC')
#                     
#                 if 'TUBE NAME' in tube_meta and 'TUBE NAME' not in self.model.show_fcs_metadata:
#                     self.model.show_fcs_metadata.append('TUBE NAME')
#                     
#                 if '$SMNO' in tube_meta and '$SMNO' not in self.model.show_fcs_metadata:
#                     self.model.show_fcs_metadata.append('$SMNO')
                    
#                 for meta in tube_meta.keys():
#                     if meta.startswith('CF_') and meta not in self.model.show_fcs_metadata:
#                         self.model.show_fcs_metadata.append(meta)
                                                       
            # check the next tube against the dummy experiment
            try:
                check_tube(path, self.model.dummy_experiment)
            except util.CytoflowError as e:
                error(None, e.__str__(), "Error importing tube")
                return
            
            meta = parse_tube(path, self.model.dummy_experiment, metadata_only = True)
                
            tube = Tube(file = path, parent = self.model, meta = meta)
            
            self.model.tubes.append(tube)
            
#             for trait in self.model.tube_traits:
#                 tube.add_trait(trait.name, trait)
#                 
#                 # this magic makes sure the trait is actually defined
#                 # in tube.__dict__, so it shows up in trait_names etc.
#                 if trait.name in meta:
#                     tube.trait_set(**{trait.name : meta[trait.name]})
#                 else:
#                     tube.trait_set(**{trait.name : trait.default_value})
#                     
#                 if trait.condition:
#                     tube.on_trait_change(self._try_multiedit, trait.name)
                
            
#             tube.trait_set(file = path, parent = self.model)
            
#             if '$SRC' in tube_meta:    
#                 self._add_metadata("$SRC", "$SRC", Str(condition = False))
#                 tube.trait_set(**{"$SRC" : tube_meta['$SRC']})
#                 
#             if 'TUBE NAME' in tube_meta:
#                 self._add_metadata("TUBE NAME", "TUBE NAME", Str(condition = False))
#                 tube.trait_set(**{"TUBE NAME" : tube_meta['TUBE NAME']})
#                 
#             if '$SMNO' in tube_meta:
#                 self._add_metadata("$SMNO", "$SMNO", Str(condition = False))
#                 tube.trait_set(**{"$SMNO" : tube_meta['$SMNO']})
#                 
#             if 'WELL ID' in tube_meta:
#                 self._add_metadata("Row", "Row", Str(condition = False))
#                 self._add_metadata("Col", "Col", Int(condition = False))
#                 
#                 pos = tube_meta['WELL ID']
#                 row = pos[0]
#                 col = int(pos[1:3])
#                 
#                 tube.trait_set(**{"Row" : row, "Col" : col})
#                 
#             if not '$SRC' in tube_meta and not 'TUBE NAME' in tube_meta:
#                 self._add_metadata('Tube', 'Tube', Str(condition = False))
#                 tube.trait_set(**{"Tube" : Path(path).stem})        
                
#             new_tubes.append(tube)

#         self.model.tubes.extend(new_tubes)
            
    def _on_remove_tubes(self):
        conf = confirm(None,
                       "Are you sure you want to remove the selected tube(s)?",
                       "Remove tubes?")
        if conf == YES:
            for (tube, _) in self.model.selected:
                self.model.tubes.remove(tube)
                
        if not self.model.tubes:
            self.model.dummy_experiment = None

    
    @on_trait_change('model:tubes_items', post_init = True)
    def _tubes_changed(self, event):
        for tube in event.added:
            for trait in self.model.tube_traits:
                tube.add_trait(trait.name, trait.trait)
                
                if trait.name in tube.meta:
                    tube.trait_set(**{trait.name : tube.meta[trait.name]})
                else:
                    tube.trait_set(**{trait.name : trait.trait.default_value})
        
#         for tube in event.removed:
#             pass
#         if self.btn_remove_tubes:
#             if len(self.model.tubes) == 0:
#                 self.btn_remove_tubes.setEnabled(False)
#                 self.btn_metadata.setEnabled(False)
#             else:
#                 self.btn_remove_tubes.setEnabled(True)
#                 self.btn_metadata.setEnabled(True)
                
    @on_trait_change('model:tube_traits_items', post_init = True)
    def _tube_traits_changed(self, event):
        for trait in event.added:
            if trait.trait_type != 'Read Only':
                self.model.counter.clear()
                
            for tube in self.model.tubes:
                tube.add_trait(trait.name, trait.trait)
                
                if trait.name in tube.meta:
                    tube.trait_set(**{trait.name : tube.meta[trait.name]})
                else:
                    tube.trait_set(**{trait.name : trait.trait.default_value})
                    
                if trait.editable:
                    tube.on_trait_change(self._try_multiedit, trait.name)
                    
                    tube.conditions[trait.name] = tube.trait_get()[trait.name]
                    tube_hash = tube.conditions_hash()
                    if tube_hash in self.model.counter:
                        self.model.counter[tube_hash] += 1
                    else:
                        self.model.counter[tube_hash] = 1
                        
            if self.table_editor:
                self.table_editor.columns.append(ExperimentColumn(name = trait.name,
                                                                  editable = trait.editable))
        
        for trait in event.removed:
            self.model.counter.clear()
            
            for tube in self.model.tubes:
                tube.remove_trait(trait.name)
                
                if trait.trait_type != 'Read Only' and trait.name not in tube.meta:
                    tube.on_trait_change(self.try_multiedit, trait.name, remove = True)
                    
                if trait.trait_type != 'Read Only':
                    del tube.conditions[trait.name]
                    
                    tube_hash = tube.conditions_hash()
                    if tube_hash in self.model.counter:
                        self.model.counter[tube_hash] += 1
                    else:
                        self.model.counter[tube_hash] = 1
                        
            table_column = next((x for x in self.table_editor.columns if x.name == trait.name))
            self.table_editor.columns.remove(table_column)
                    
                
                
                
#     @on_trait_change('model:show_fcs_metadata_items', post_init = True)
#     def _fcs_metadata_items(self, event):
#         for meta_name in event.added:
#             self._add_metadata(meta_name, meta_name, Str(condition = False))
#             
#         for meta_name in event.removed:
#             self._remove_metadata(meta_name)

            
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
        
#     def _add_metadata(self, name, label, trait):
#         """
#         Add a new tube metadata
#         """
#         
#         if trait.condition:
#             self.model.counter.clear()
#             
#         trait_names = [x.name for x in self.model.tube_traits]
#             
#         if not name in trait_names:
#             self.model.tube_traits.append(trait)
#             
#             for tube in self.model.tubes:
#                 tube.add_trait(name, trait)
# 
#                 # this magic makes sure the trait is actually defined
#                 # in tube.__dict__, so it shows up in trait_names etc.                
#                 if name in tube.meta:
#                     tube.trait_set(**{name : tube.meta[name]})
#                 else:
#                     tube.trait_set(**{name : trait.default_value})
#                     tube.on_trait_change(self._try_multiedit, name)
# 
#                 if trait.condition:                    
#                     tube.conditions[name] = tube.meta[name] if name in tube.meta else trait.default_value
#                     
#                     tube_hash = tube.conditions_hash()
#                     if tube_hash in self.model.counter:
#                         self.model.counter[tube_hash] += 1
#                     else:
#                         self.model.counter[tube_hash] = 1
# 
#             self.table_editor.columns.append(ExperimentColumn(name = name,
#                                                               label = label,
#                                                               editable = trait.condition))
#             
#     def _remove_metadata(self, name):
#         self.model.counter.clear()
#         trait = next(x for x in self.model.tube_traits if x.name == name)
#         
#         self.model.tube_traits.remove(trait)
#              
#         for tube in self.model.tubes:
#             tube.remove_trait(name)
# 
#             if name not in tube.meta:
#                 tube.on_trait_change(self._try_multiedit, name, remove = True)
# 
#             if tube.trait(name).condition:
#                 del tube.conditions[name]
# 
#                 tube_hash = tube.conditions_hash()
#                 if tube_hash in self.model.counter:
#                     self.model.counter[tube_hash] += 1
#                 else:
#                     self.model.counter[tube_hash] = 1   
#                 
#         table_column = next((x for x in self.table_editor.columns if x.name == name))
#         self.table_editor.columns.remove(table_column)
        
        
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
        
        btn_add_tubes = QtGui.QPushButton("Add tubes...")
        layout.addWidget(btn_add_tubes, 0, 0)
        QtCore.QObject.connect(btn_add_tubes, QtCore.SIGNAL('clicked()'),
                               self.handler._on_add_tubes)
        
        btn_remove_tubes = QtGui.QPushButton("Remove tubes")
        layout.addWidget(btn_remove_tubes, 1, 0)
        QtCore.QObject.connect(btn_remove_tubes, QtCore.SIGNAL('clicked()'),
                               self.handler._on_remove_tubes)
        btn_remove_tubes.setEnabled(len(self.model.tubes) > 0)
        self.handler.btn_remove_tubes = btn_remove_tubes

        # start disabled if there aren't any tubes in the model
        btn_metadata = QtGui.QPushButton("Edit metadata...")
        layout.addWidget(btn_metadata, 0, 1)
        QtCore.QObject.connect(btn_metadata, QtCore.SIGNAL('clicked()'),
                               self.handler._on_edit_metadata)
        btn_metadata.setEnabled(len(self.model.tubes) > 0)
        self.handler.btn_metadata = btn_metadata
        
        btn_import = QtGui.QPushButton("Import from CSV...")
        layout.addWidget(btn_import, 1, 1)
        QtCore.QObject.connect(btn_import, QtCore.SIGNAL('clicked()'),
                               self.handler._on_import)
#         btn_import.setEnabled(True)
        
        layout.addItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Maximum), 0, 2)
        layout.addItem(QtGui.QSpacerItem(0, 0, QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Maximum), 1, 2)
        
        # 'OK' button.
        btn_ok = QtGui.QPushButton("OK")
        btn_ok.setDefault(True)
        layout.addWidget(btn_ok, 0, 3)
        QtCore.QObject.connect(btn_ok, QtCore.SIGNAL('clicked()'),
                               self.control, QtCore.SLOT('accept()'))
        
        # 'Cancel' button.
        btn_cancel = QtGui.QPushButton("Cancel")
        layout.addWidget(btn_cancel, 1, 3)
        QtCore.QObject.connect(btn_cancel, QtCore.SIGNAL('clicked()'),
                               self.control, QtCore.SLOT('reject()'))   
        
        # add the button container to the widget     
        buttons.setLayout(layout)
        return buttons
    
    def _create_dialog_area(self, parent):
         
        self.ui = self.model.edit_traits(view = 'default_view',
                                         kind='subpanel', 
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
    
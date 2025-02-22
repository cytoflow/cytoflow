#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2022
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
cytoflowgui.import_dialog
-------------------------

A modal dialog that allows the user to set up their experiment, mapping
FCS files to experimental conditions.

There are a few main classes:

- `Tube` -- represents one tube (well, an FCS file) in an experiment -- the filename
  and its metadata.

- `TubeTrait` -- represents one trait (the trait type and name)

- `ExperimentDialogModel` -- the tabular model of tubes, traits, and trait values

- `ExperimentDialogHandler` -- the controller which contains the view and the
  logic for connecting it to the model.
  
Additionally, there are several utility functions and classes: 

- `not_true` and `not_false` -- obvious

- `sanitize_metadata` -- replaces all non-Python-safe characters in a tube's 
  metadata with '_'
  
- `eval_bool` -- interprets various strings as True or False

- `ConvertingBool` -- trait type that uses `eval_bool` to convert strings 
  to boolean values
"""

# for local debugging
if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"
    

from pathlib import Path
import pandas
        
from traits.api import (HasStrictTraits, Instance, Str, Int, List, Bool, Enum, 
                        Property, CStr, observe, Dict, Event,
                        cached_property, CFloat, BaseCBool, TraitError)
                       
from traitsui.api import (View, Item, TableEditor, Controller, InstanceEditor, 
                          HGroup, ButtonEditor, EnumEditor, TextEditor, VGroup, 
                          Label)

from traitsui.menu import OKCancelButtons

from traitsui.qt.table_editor import TableEditor as TableEditorQt

from pyface.api import FileDialog, error, warning, confirm, YES  # @UnresolvedImport

from pyface.constant import OK as PyfaceOK

from traitsui.table_column import ObjectColumn

from cytoflow import Tube as CytoflowTube
from cytoflow import Experiment, ImportOp
from cytoflow.operations.import_op import check_tube, parse_tube
from cytoflowgui.workflow.operations.import_op import ValidPythonIdentifier
import cytoflow.utility as util

from cytoflowgui.editors import VerticalListEditor

def not_true ( value ):
    return (value is not True)

def not_false ( value ):
    return (value is not False)

def sanitize_metadata(meta):
    """replaces all non-Python-safe characters in a tube's metadata with '_'"""
    ret = {}
    for k, v in meta.items():
        if len(k) > 0 and k[0] == '$':
            k = k[1:]
        k = util.sanitize_identifier(k)
        ret[k] = v
        
    return ret

class Tube(HasStrictTraits):
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
    
    We also derive traits from tubes' FCS metadata.  One can make a new column
    from metadata, then convert it into a condition to use in the analysis.
    
    We also use the "transient" flag to specify traits that shouldn't be 
    displayed in the editor.  This matches well with the traits that
    every HasTraits-derived class has by default (all of which are transient.)
    """
    
    # these are the traits that every tube has.  every other trait is
    # dynamically created. 
    
    index = Property(Int)
    """The tube index"""
    
    file = Str(transient = True)
    """The FCS filename"""
    
    # need a link to the model; needed for row coloring
    parent = Instance("ExperimentDialogModel", transient = True)
    """Which model are we part of?"""
    
    # Remember that we store conditions as traits on this instance.
    # we store them here too for fast hashing
    conditions = Dict
    """A Dict of the conditions (for hashing)"""
    
    metadata = Dict
    """The FCS metadata"""
    
    all_conditions_set = Property(Bool, depends_on = "conditions")
    """Do all of the conditions have a value?"""
            
    def conditions_hash(self):
        """Return a hash of this tube's conditions (for equality testing)"""
        
        ret = int(0)
    
        for key, value in self.conditions.items():
            if not ret:
                ret = hash((key, value))
            else:
                ret = ret ^ hash((key, value))
                
        return ret
    
    def _anytrait_changed(self, name, old, new):
        if self.parent is not None and name in self.parent.tube_traits_dict and self.parent.tube_traits_dict[name].type != 'metadata':
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
    
    # magic - gets the value of the 'index' property
    def _get_index(self):
        return self.parent.tubes.index(self)
    
    
class ExperimentColumn(ObjectColumn):
    """A `traitsui.table_column.ObjectColumn` with setable color"""
     
    # override ObjectColumn.get_cell_color
    def get_cell_color(self, obj):
        if not self.is_editable(obj):
            return 'light grey'
        
        if obj.parent.is_tube_unique(obj) and obj.all_conditions_set:
            return super(ObjectColumn, self).get_cell_color(object)
        else:
            return 'pink'
        
    def _get_label(self):
        """ Gets the label of the column.
        """
        if self._label is not None:
            return self._label
        return self.name
    
    
def eval_bool(x):
    """
    Evaluate "f", "false", "n" or "no" as `False`; 
    and "t", "true", "y" or "yes" as `True`
    """
    
    try:
        xc = x.casefold()
        if xc == 'f' or xc == 'false' or xc == 'n' or xc == 'no':
            return False
        elif xc == 't' or xc == 'true' or xc == 'y' or xc == 'yes':
            return True
        else:
            return bool(x)
    except:
        return bool(x)
    
    
class ConvertingBool(BaseCBool):
    """
    A trait that converts "f", "false", "n", or "no" to `False`
    and "t", "true", "y" or "yes" to `True`
    """
    
    evaluate = eval_bool
    
    def validate ( self, _, name, value ):
        try:
            return eval_bool( value )
        except:
            self.error( object, name, value )
            
    
class TubeTrait(HasStrictTraits):
    """
    A class representing a trait on a tube.  A trait has an underlying
    `traits.trait_type.TraitType`, a name, a type ("metadata", "category",
    "float" or "bool"), and a default view. 
    """
    
    model = Instance('ExperimentDialogModel')
    """Which model are we a part of?"""

    trait = Property
    """The `traits.trait_type.TraitType` that underlies this trait"""
    
    name = ValidPythonIdentifier
    """The name of the trait"""
    
    type = Enum(['metadata', 'category', 'float', 'bool'])
    """What type of trait is it?"""
        
    remove_trait = Event
    
    default_view = View(HGroup(Item('type',
                                    editor = EnumEditor(values = {'metadata' : "FCS Metadata",
                                                                  'category' : "Category",
                                                                  'float' : "Number",
                                                                  'bool' : "True/False"})),
                               Item('name',
                                    editor = TextEditor(auto_set = False),
                                    visible_when = 'type != "metadata"'),
                               Item('name',
                                    editor = EnumEditor(name = 'object.model.fcs_metadata'),
                                    visible_when = 'type == "metadata"')))
    
    
    # magic - gets values for the `trait` property
    def _get_trait(self):
        if self.type == 'metadata' or self.type == 'category':
            return CStr()
        elif self.type == 'float':
            return CFloat()
        elif self.type == 'bool':
            return ConvertingBool()

    
class ExperimentDialogModel(HasStrictTraits):
    """
    The model for the Experiment setup dialog.
    """

    tubes = List(Tube)
    """The list of Tubes (rows in the table)"""

    tube_traits = List(TubeTrait)
    """A list of the traits that have been added to Tube instances (columns in the table)"""
    
    tube_traits_dict = Dict
    """A dictionary of trait name --> TubeTrait instances"""
    
    counter = Dict(Int, Int)
    """
    A dictionary of tube hash --> # of tubes with that hash;
    keeps track of whether a tube is unique or not
    """

    valid = Property(List)
    """Are all the tubes unique and filled?"""
    
    dummy_experiment = Instance(Experiment)
    """
    A dummy Experiment, with the first Tube and no events, so we can check
    subsequent tubes for voltage etc. and fail early.
    """
    
    # traits to communicate with the traits_view
    fcs_metadata = Property(List, depends_on = 'tubes')
    
    def init(self, import_op):    
        """
        Initializes the model from a pre-existing `ImportOp`
        """
        
        if 'CF_File' not in import_op.conditions:
            self.tube_traits.append(
                TubeTrait(model = self, type = 'metadata', name = 'CF_File'))    
            
        for name, condition in import_op.conditions.items():
            if condition == "category" or condition == "object":
                self.tube_traits.append(TubeTrait(model = self, name = name, type = 'category'))
            elif condition == "int" or condition == "float":
                self.tube_traits.append(TubeTrait(model = self, name = name, type = 'float'))
            elif condition == "bool":
                self.tube_traits.append(TubeTrait(model = self, name = name, type = 'bool'))

        self.dummy_experiment = None
        
        if import_op.tubes:
            try:
                self.dummy_experiment = import_op.apply(metadata_only = True)
            except Exception as e:
                warning(None,
                        "Had trouble loading some of the experiment's FCS "
                        "files.  You will need to re-add them.\n\n{}".format(str(e)))
                return        
        
            for op_tube in import_op.tubes:    
                metadata = self.dummy_experiment.metadata['fcs_metadata'][op_tube.file]
                tube = Tube(file = op_tube.file, 
                            parent = self, 
                            metadata = sanitize_metadata(metadata))
                                                     
                self.tubes.append(tube)  # adds the dynamic traits to the tube
                
                tube.trait_set(**op_tube.conditions)
                
                for trait in self.tube_traits:
                    if trait.type == 'metadata':
                        tube.trait_set(**{trait.name : tube.metadata[trait.name]})
                    else:
                        tube.conditions[trait.name] = tube.trait_get()[trait.name]
    
    
    @observe('tubes:items')
    def _tubes_items(self, event):
        for tube in event.added:
            for trait in self.tube_traits:
                if not trait.name:
                    continue
                
                tube.add_trait(trait.name, trait.trait)
                
                if trait.type == 'metadata':
                    tube.trait_set(**{trait.name : tube.metadata[trait.name]})
                else:
                    tube.trait_set(**{trait.name : trait.trait.default_value})
                    tube.conditions[trait.name] = tube.trait_get()[trait.name]  
            
        self.counter.clear()
        for tube in self.tubes:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1
                 
    @observe('tube_traits:items')
    def _tube_traits_changed(self, event):
        for trait in event.added:
            if not trait.name:
                continue
                
            for tube in self.tubes:
                tube.add_trait(trait.name, trait.trait)
                
                if trait.type == 'metadata':
                    tube.trait_set(**{trait.name : tube.metadata[trait.name]})
                else:
                    tube.trait_set(**{trait.name : trait.trait.default_value})
                    tube.conditions[trait.name] = tube.trait_get()[trait.name]
    
            self.tube_traits_dict[trait.name] = trait
             
        for trait in event.removed:
            if not trait.name:
                continue
            
            for tube in self.tubes:
                tube.remove_trait(trait.name)

                if trait.type != 'metadata':
                    del tube.conditions[trait.name]

            del self.tube_traits_dict[trait.name]
            
        self.counter.clear()
        for tube in self.tubes:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1
            
    @observe('tube_traits:items:name')
    def _on_trait_name_change(self, event):
        trait = event.object
        old_name = event.old
        new_name = event.new
        for tube in self.tubes:
            trait_value = None
            
            if old_name:
                # store the value
                trait_value = tube.trait_get()[old_name]
                
                if trait.type != 'metadata':                        
                    del tube.conditions[old_name]
                
                # defer removing the old trait until the handler
                # tube.remove_trait(old_name)
                
            if new_name:
                if new_name in tube.metadata:
                    trait_value = tube.metadata[new_name]
                elif trait_value is None:
                    trait_value = trait.trait.default_value
                
                tube.add_trait(new_name, trait.trait)
                tube.trait_set(**{new_name : trait_value})
                
                if trait.type != 'metadata':
                    tube.conditions[new_name] = trait_value
                
        if old_name:
            del self.tube_traits_dict[old_name]
            
        if new_name:
            self.tube_traits_dict[new_name] = trait

        self.counter.clear()
        for tube in self.tubes:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1
                
                
    @observe('tube_traits:items:type')
    def _on_type_change(self, event):
        trait = event.object
        old_type = event.old
        new_type = event.new

        if not trait.name:
            return
                
        for tube in self.tubes:
            trait_value = tube.trait_get()[trait.name]
            tube.remove_trait(trait.name)
            if old_type != 'metadata':
                del tube.conditions[trait.name]
                
            tube.add_trait(trait.name, trait.trait)
            
            try:
                tube.trait_set(**{trait.name : trait_value})
            except TraitError:
                tube.trait_set(**{trait.name : trait.trait.default_value})
            if new_type != 'metadata':
                tube.conditions[trait.name] = tube.trait_get()[trait.name]
            
        self.counter.clear()
        for tube in self.tubes:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.counter:
                self.counter[tube_hash] += 1
            else:
                self.counter[tube_hash] = 1
                
    
    def update_import_op(self, import_op):
        """
        Update an `ImportOp` with the information in this dialog
        """
        
        if not self.tubes:
            return
        
        assert self.dummy_experiment is not None
        
        conditions = {trait.name : trait.type for trait in self.tube_traits
                      if trait.type != 'metadata'}
            
        tubes = []
        events = 0
        for tube in self.tubes:
            op_tube = CytoflowTube(file = tube.file,
                                   conditions = tube.trait_get(list(conditions.keys())))
            tubes.append(op_tube)
            events += tube.metadata['TOT']
            
        import_op.ret_events = events
            
        import_op.conditions = conditions
        import_op.tubes = tubes   
        import_op.original_channels = channels = self.dummy_experiment.channels
        
        all_present = len(import_op.channels_list) > 0
        if len(import_op.channels_list) > 0:
            for c in import_op.channels_list:
                if c.name not in channels:
                    all_present = False
                    
            if not all_present:
                warning(None,
                        "Some of the operation's channels weren't found in "
                        "these FCS files.  Resetting all channel names.",
                        "Resetting channel names")
        
        if not all_present:
            import_op.reset_channels()        
        
            
    def is_tube_unique(self, tube):
        """
        Is a tube unique?
        """
        
        tube_hash = tube.conditions_hash()
        if tube_hash in self.counter:
            return self.counter[tube.conditions_hash()] == 1
        else:
            return False
    
    
    def _get_valid(self):
        return len(self.tubes) > 0 and \
               len(set(self.counter)) == len(self.tubes) and \
               all([x.all_conditions_set for x in self.tubes])
    
    
    # magic: gets the list of FCS metadata for the trait list editor
    @cached_property
    def _get_fcs_metadata(self):
        meta = {}
        for tube in self.tubes:
            for name, val in tube.metadata.items():
                if name not in meta:
                    meta[name] = set()
                    
                meta[name].add(val)
                
        ret = [x for x in meta.keys() if len(meta[x]) > 1]
            
        return sorted(ret)
    
                    
class ExperimentDialogHandler(Controller):
    """
    A controller that contains the import dialog's view and the logic that 
    connects it to the `ExperimentDialogModel`
    """
    
    # bits for model initialization
    import_op = Instance('cytoflowgui.workflow.operations.import_op.ImportWorkflowOp')
        
    # events
    add_tubes = Event
    remove_tubes = Event
    add_variable = Event
    import_csv = Event
    
    # traits to communicate with the TabularEditor
    selected_tubes = List
    
    default_view = View(
            HGroup(
                VGroup(
                    Label("Variables"),
                    Item('tube_traits',
                         editor = VerticalListEditor(editor = InstanceEditor(),
                                                     style = 'custom',
                                                     mutable = False,
                                                     deletable = True),
                         show_label = False),
                    HGroup(
                        Item('handler.add_variable',
                             editor = ButtonEditor(label = "Add a variable"),
                             show_label = False))),
                VGroup(
                    Label("Tubes"),
                    Item(name = 'tubes', 
                         id = 'table', 
                         editor = TableEditor(editable = True,
                                              sortable = True,
                                              auto_size = True,
                                              configurable = False,
                                              selection_mode = 'rows',
                                              selected = 'handler.selected_tubes',
                                              columns = [ObjectColumn(name = 'index',
                                                                      read_only_cell_color = 'light grey',
                                                                      editable = False)]),
                         enabled_when = "object.tubes",
                         show_label = False),
                    HGroup(
                        Item('handler.add_tubes',
                             editor = ButtonEditor(label = "Add tubes..."),
                             show_label = False),
                        Item('handler.remove_tubes',
                             editor = ButtonEditor(label = "Remove tubes"),
                             show_label = False,
                             enabled_when = 'object.tubes'),
                        Item('handler.import_csv',
                             editor = ButtonEditor(label = "Import from CSV..."),
                             show_label = False)))),
            title     = 'Experiment Setup',
            buttons = OKCancelButtons,
            resizable = True
        )

    # keep a ref to the table editor so we can add columns dynamically
    table_editor = Instance(TableEditorQt)
    
    updating = Bool(False)
    
    def init(self, info):
        
        # save a reference to the table editor
        self.table_editor = info.ui.get_editors('tubes')[0]
        
        # init the model
        self.model.init(self.import_op)
                
        return True
    
    def close(self, info, is_ok):
        """
        Handles the user attempting to close a dialog-based user interface.

        This method is called when the user attempts to close a window, by
        clicking an **OK** or **Cancel** button, or clicking a Close control
        on the window). It is called before the window is actually destroyed.
        Override this method to perform any checks before closing a window.

        While Traits UI handles "OK" and "Cancel" events automatically, you
        can use the value of the *is_ok* parameter to implement additional
        behavior.

        Parameters
        ----------
        info : UIInfo object
            The UIInfo object associated with the view
        is_ok : Boolean
            Indicates whether the user confirmed the changes (such as by
            clicking **OK**.)

        Returns
        -------
        allow_close : bool
            A Boolean, indicating whether the window should be allowed to close.
        """
        if is_ok:
            if not self.model.valid:
                error(None, 
                      "Each tube must have a unique set of experimental conditions",
                      "Invalid experiment!")
                return False

        if not is_ok:
            # we don't need to "undo" anything, we're throwing this model away
            info.ui.history = None

        return True
    
    
    def closed(self, info, is_ok):
        for trait in self.model.tube_traits:
            if trait.type != 'metadata':
                for tube in self.model.tubes:
                    tube.on_trait_change(self._try_multiedit, 
                                         trait.name, 
                                         remove = True)
        if is_ok:
            self.model.update_import_op(self.import_op)
        
            
    @observe('add_variable')
    def _on_add_variable(self, _):
        self.model.tube_traits.append(TubeTrait(model = self.model))
        
            
    @observe('import_csv')
    def _on_import(self, _):
        """
        Import format: CSV, first column is filename, path relative to CSV.
        others are conditions, type is autodetected.  first row is header
        with names.
        """
        file_dialog = FileDialog()
        file_dialog.wildcard = "CSV files (*.csv)|*.csv|"
        file_dialog.action = 'open'
        file_dialog.open()
        
        if file_dialog.return_code != PyfaceOK:
            return
        
        try:
            csv = pandas.read_csv(file_dialog.path)
        except Exception as e:
            warning(None, "Had trouble reading the CSV file: {}".format(str(e)))
            return
            
        csv_folder = Path(file_dialog.path).parent
        
        if self.model.tubes or self.model.tube_traits:
            if confirm(parent = None,
                       message = "This will clear the current conditions and tubes! "
                                 "Are you sure you want to continue?",
                       title = "Clear tubes and conditions?") != YES:
                return
        
        for col in csv.columns[1:]:
            self.model.tube_traits.append(TubeTrait(model = self.model,
                                                    name = util.sanitize_identifier(col),
                                                    type = 'category'))
            
        for i, row in csv.iterrows():
            try:
                filename = csv_folder / row[0]
            except Exception as e:
                warning(None, "Had trouble parsing row {}\n{}\nIs your CSV file formatted correctly?".format(i+2, str(e)))
                return
            
            try:
                metadata, _ = parse_tube(str(filename), metadata_only = True)
            except Exception as e:
                warning(None, "Had trouble loading file {}: {}".format(filename, str(e)))
                return
            
            # if we're the first tube loaded, create a dummy experiment
            # and setup default metadata columns
            if not self.model.dummy_experiment:
                self.model.dummy_experiment = \
                    ImportOp(tubes = [CytoflowTube(file = filename)]).apply(metadata_only = True)
                                                       
            # check the next tube against the dummy experiment
            try:
                check_tube(filename, self.model.dummy_experiment)
            except util.CytoflowError as e:
                error(None, e.__str__(), "Error importing tube")
                return

            metadata['CF_File'] = Path(filename).stem
            new_tube = Tube(file = str(filename), parent = self.model, metadata = sanitize_metadata(metadata))
            self.model.tubes.append(new_tube)

            for col in csv.columns[1:]:
                new_tube.trait_set(**{util.sanitize_identifier(col) : row[col]})
                
    @observe('add_tubes')
    def _on_add_tubes(self, _):
        """
        Handle "Add tubes..." button.  Add tubes to the experiment.
        """
        
        file_dialog = FileDialog()
        file_dialog.wildcard = "Flow cytometry files (*.fcs *.lmd)|*.fcs *.lmd|"
        file_dialog.action = 'open files'
        file_dialog.open()
        
        if file_dialog.return_code != PyfaceOK:
            return
        
        for path in file_dialog.paths:
            try:
                metadata, _ = parse_tube(path, metadata_only = True)
            except Exception as e:
                raise RuntimeError("FCS reader threw an error on tube {0}: {1}"\
                                   .format(path, str(e)))
                
            # if we're the first tube loaded, create a dummy experiment
            # and setup default metadata columns
            if not self.model.dummy_experiment:
                self.model.dummy_experiment = \
                    ImportOp(tubes = [CytoflowTube(file = path)]).apply(metadata_only = True)
                                                       
            # check the next tube against the dummy experiment
            try:
                check_tube(path, self.model.dummy_experiment)
            except util.CytoflowError as e:
                error(None, str(e), "Error importing tube")
                return
            
            metadata['CF_File'] = Path(path).stem    
            tube = Tube(file = path, parent = self.model, metadata = sanitize_metadata(metadata))
            
            self.model.tubes.append(tube)
            
            for trait in self.model.tube_traits:
                if trait.type != 'metadata' and trait.name:
                    tube.on_trait_change(self._try_multiedit, trait.name)
         
            
    @observe('remove_tubes')
    def _on_remove_tubes(self, _):
        conf = confirm(None,
                       "Are you sure you want to remove the selected tube(s)?",
                       "Remove tubes?")
        if conf == YES:
            for tube in self.selected_tubes:
                self.model.tubes.remove(tube)
            self.selected_tubes = []
                
        if not self.model.tubes:
            self.model.dummy_experiment = None

                
    @observe('model:tube_traits:items', post_init = True)
    def _tube_traits_changed(self, event):
        for trait in event.added:
            if not trait.name:
                continue
            
            if self.table_editor:
                self.table_editor.columns.append(ExperimentColumn(name = trait.name,
                                                                  editable = (trait.type != 'metadata')))                 
            for tube in self.model.tubes:   
                if trait.type != 'metadata' and trait.name:
                    tube.on_trait_change(self._try_multiedit, trait.name)

        for trait in event.removed:
            if not trait.name:
                continue
            
            table_column = next((x for x in self.table_editor.columns if x.name == trait.name))
            self.table_editor.columns.remove(table_column)
            
            for tube in self.model.tubes:
                if trait.type != 'metadata' and trait.name:
                    tube.on_trait_change(self._try_multiedit, trait.name, remove = True)
                    
                    
    @observe('model:tube_traits:items:name')
    def _tube_trait_name_changed(self, event):
    #def _tube_trait_name_changed(self, trait, _, old_name, new_name):
        trait = event.object
        old_name = event.old
        new_name = event.new
        
        if old_name:
            old_table_column = next((x for x in self.table_editor.columns if x.name == old_name))
            column_idx = self.table_editor.columns.index(old_table_column)
        else:
            column_idx = len(self.table_editor.columns)
                
        if new_name:
            self.table_editor.columns.insert(column_idx,
                                             ExperimentColumn(name = new_name,
                                                              editable = (trait.type != 'metadata')))
            
        if old_name:          
            self.table_editor.columns.remove(old_table_column)
               
        for tube in self.model.tubes:   
            if trait.type != 'metadata':
                if old_name:
                    tube.on_trait_change(self._try_multiedit, old_name, remove = True)
                    
                if new_name:
                    tube.on_trait_change(self._try_multiedit, new_name)
                
            if old_name:
                tube.remove_trait(old_name)
                
            
        self.model.counter.clear()
        for tube in self.model.tubes:
            tube_hash = tube.conditions_hash()
            if tube_hash in self.model.counter:
                self.model.counter[tube_hash] += 1
            else:
                self.model.counter[tube_hash] = 1
                
    @observe('model:tube_traits:items:type')
    def _tube_trait_type_changed(self, event):
    #def _tube_trait_type_changed(self, trait, _, old_type, new_type):
        trait = event.object
        old_type = event.old
        new_type = event.new
        
        if not trait.name:
            return
        
        table_column = next((x for x in self.table_editor.columns if x.name == trait.name))
        
        table_column.editable = (new_type != 'metadata')  
        
        for tube in self.model.tubes:
            if trait.name:
                if old_type != 'metadata':
                    tube.on_trait_change(self._try_multiedit, trait.name, remove = True)
                    
                if new_type != 'metadata':
                    tube.on_trait_change(self._try_multiedit, trait.name)
                  
                    
            
    def _try_multiedit(self, obj, name, old, new):
        """
        See if there are multiple elements selected when a tube's trait changes
        
        and if so, edit the same trait for all the selected tubes.
        """
        
        if self.updating:
            return
        
        self.updating = True

        for tube in self.selected_tubes:
            if tube != obj:
                old_hash = tube.conditions_hash()
                self.model.counter[old_hash] -= 1
                if self.model.counter[old_hash] == 0:
                    del self.model.counter[old_hash]            
    
                # update the underlying traits without notifying the editor
                # we do this all here for performance reasons
                tube.trait_setq(**{name: new})
                tube.conditions[name] = new
                
                new_hash = tube.conditions_hash()
                if new_hash not in self.model.counter:
                    self.model.counter[new_hash] = 1
                else:
                    self.model.counter[new_hash] += 1
                

        # now refresh the editor all at once
        self.table_editor.refresh_editor()
        self.updating = False
        

    
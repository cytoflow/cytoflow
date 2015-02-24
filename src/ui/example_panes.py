'''
Created on Feb 23, 2015

@author: brian
'''
# Standard library imports.
import os.path

# Enthought library imports.
from pyface.api import PythonEditor
from pyface.tasks.api import TaskPane, TraitsDockPane
from traits.api import Event, File, Instance, List, Str
from traitsui.api import View, Item, FileEditor


class FileBrowserPane(TraitsDockPane):
    """ A simple file browser pane.
    """

    #### TaskPane interface ###################################################

    id = 'example.file_browser_pane'
    name = 'File Browser'

    #### FileBrowserPane interface ############################################

    # Fired when a file is double-clicked.
    activated = Event

    # The list of wildcard filters for filenames.
    filters = List(Str)

    # The currently selected file.
    selected_file = File(os.path.expanduser('~'))

    # The view used to construct the dock pane's widget.
    view = View(Item('selected_file',
                     editor=FileEditor(dclick_name='activated',
                                       filter_name='filters'),
                     style='custom',
                     show_label=False),
                resizable=True)


class PythonScriptBrowserPane(FileBrowserPane):
    """ A file browser pane restricted to Python scripts.
    """

    #### TaskPane interface ###################################################

    id = 'example.python_script_browser_pane'
    name = 'Script Browser'

    #### FileBrowserPane interface ############################################

    filters = [ '*.py' ]


class PythonEditorPane(TaskPane):
    """ A wrapper around the Pyface Python editor.
    """

    #### TaskPane interface ###################################################

    id = 'example.python_editor_pane'
    name = 'Python Editor'

    #### PythonEditorPane interface ###########################################

    editor = Instance(PythonEditor)

    ###########################################################################
    # 'ITaskPane' interface.
    ###########################################################################

    def create(self, parent):
        self.editor = PythonEditor(parent)
        self.control = self.editor.control

    def destroy(self):
        self.editor.destroy()
        self.control = self.editor = None
        

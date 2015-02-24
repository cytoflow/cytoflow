"""
Created on Feb 23, 2015

@author: brian
"""
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traits.api import Event, File, List, Str
from traitsui.api import View, Item, FileEditor

class FlowTraitsPane(TraitsDockPane):
    """
    classdocs
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.flow_traits_pane'
    name = 'File Browser'

    #### FileBrowserPane interface ########################################

    # Fired when a file is double-clicked.
    activated = Event

    # The list of wildcard filters for filenames.
    filters = List(Str)

    # The currently selected file.
    selected_file = File

    # The view used to construct the dock pane's widget.
    view = View(Item('selected_file',
                     editor=FileEditor(dclick_name='activated',
                                       filter_name='filters'),
                     style='custom',
                     show_label=False),
                resizable=True)
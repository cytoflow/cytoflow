"""
Created on Mar 15, 2015

@author: brian
"""

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from cytoflowgui.workflow_item import WorkflowItem
from traitsui.api import Action, View, Item
from traits.api import Button, Str

class ImportWorkflowItem(WorkflowItem):
    """
    A WorkflowItem that handles importing data and making a new Experiment
    """
    name = Str("Import data")
    id = Str("")
    import_event = Button(label="Import data...")

    traits_view = View(Item(name='import_event',
                            show_label=False))
    
    def _import_event_fired(self):
        """
        Import data; save as self.result
        """
        print "pressed import"
        pass
    
if __name__ == '__main__':
    wf = ImportWorkflowItem()
    wf.configure_traits()
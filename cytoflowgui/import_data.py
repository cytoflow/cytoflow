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

class ImportWorkflowItem(WorkflowItem):
    """
    A WorkflowItem that handles importing data and making a new Experiment
    """

    import_action = Action(name = "Import data set...",
                           action = "do_import")

    traits_view = View(buttons = [import_action])
    
    def do_import(self):
        pass
    
if __name__ == '__main__':
    wf = ImportWorkflowItem()
    wf.configure_traits()
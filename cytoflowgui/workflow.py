if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traits.api import HasTraits, Instance, ListInstance, List
from traitsui.api import Handler, View, Item

from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflowgui.vertical_notebook_editor import VerticalNotebookEditor
from cytoflow.views.i_view import IView
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.import_data import ImportWorkflowItem


class Workflow(HasTraits):
    """
    A list of WorkflowItems.
    """

    workflow = List(WorkflowItem)
    
    traits_view = View(Item(name='workflow',
                            id='table',
                            editor=VerticalNotebookEditor(page_name='.operation.name',
                                                          page_description='.operation.id',
                                                          view = 'traits_view',
                                                          scrollable = True,
                                                          multiple_open = False)
                            ),
                       resizable = True
                       )
    
if __name__ == '__main__':
    wf = Workflow()
    i = ImportWorkflowItem()
    j = ImportWorkflowItem()
    wf.workflow.append(i)
    wf.workflow.append(j)
    wf.configure_traits()
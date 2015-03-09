from pyface.tasks.api import DockPane, IDockPane
from traits.has_traits import provides

@provides(IDockPane)
class WorkflowPane(DockPane):
    
    id = 'edu.mit.synbio.workflow_pane'
    name = 'Workflow Pane'
    
    def create_contents(self, parent):
        return QtGiu.QWidget(parent)
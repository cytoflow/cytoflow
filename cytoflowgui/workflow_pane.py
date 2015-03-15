from pyface.tasks.api import DockPane, IDockPane
from traits.api import provides, Instance
from pyface.qt import QtGui
from cytoflowgui.workflow import Workflow
from traitsui.api import View, UI
from pyface.action.api import ToolBarManager



@provides(IDockPane)
class WorkflowDockPane(DockPane):
    
    id = 'edu.mit.synbio.workflow_pane'
    name = "Workflow"
    
    # the workflow this pane is displaying
    model = Instance(Workflow)
    
    # the UI object associated with the TraitsUI view
    ui = Instance(UI)
    
    # an empty, unitialized view
    empty_view = View()
    
    ###########################################################################
    # 'ITaskPane' interface.
    ###########################################################################

    def destroy(self):
        """ 
        Destroy the toolkit-specific control that represents the pane.
        """
        # Destroy the Traits-generated control inside the dock control.
        if self.ui is not None:
            self.ui.dispose()
            self.ui = None

        # Destroy the dock control.
        super(WorkflowDockPane, self).destroy()

    ###########################################################################
    # 'IDockPane' interface.
    ###########################################################################

    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
        if self.model is not None:
            self.ui = self.model.edit_traits(kind='subpanel', parent=parent)
            return self.ui.control
        else:
            self.ui = self.edit_traits(kind='subpanel', parent=parent, view='empty_view')
            return self.ui.control
    
    ### TODO - rebuild/refresh when self.view is changed.
    def _workflow_changed(self):
        pass   
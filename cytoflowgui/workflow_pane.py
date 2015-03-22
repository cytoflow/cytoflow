from pyface.tasks.api import DockPane, IDockPane, Task
from traits.api import provides, Instance, List
from pyface.qt import QtGui
from cytoflowgui.workflow import Workflow
from traitsui.api import View, UI
from pyface.action.api import ToolBarManager
from envisage.api import Application
from pyface.tasks.action.api import TaskAction
from cytoflowgui.op_plugins import OP_PLUGIN_EXT, IOperationPlugin


@provides(IDockPane)
class WorkflowDockPane(DockPane):
    
    id = 'edu.mit.synbio.workflow_pane'
    name = "Workflow"
    
    # the workflow this pane is displaying
    model = Instance(Workflow)
    
    # the UI object associated with the TraitsUI view
    ui = Instance(UI)
    
    # the application instance from which to get plugin instances
    plugins = List(IOperationPlugin)
    
    # the task serving as the dock pane's controller
    task = Instance(Task)
        
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
        """ 
        Create and return the toolkit-specific contents of the dock pane.
        """
 
        self.toolbar = ToolBarManager(orientation='vertical', 
                                      image_size = (32, 32))
                 
        for plugin in self.plugins:
            task_action = TaskAction(name=plugin.short_name,
                                     on_perform = lambda: self.task.add_operation(plugin.id))
            self.toolbar.append(task_action)
             
        window = QtGui.QMainWindow()
        window.addToolBar(self.toolbar.create_tool_bar(window))
         
        self.ui = self.model.edit_traits(kind='subpanel', parent=window)
        window.setCentralWidget(self.ui.control)
         
        window.setParent(parent)
        parent.setWidget(window)
         
        return window

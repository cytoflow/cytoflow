from pyface.tasks.api import DockPane, IDockPane, Task
from traits.api import provides, Instance
from pyface.qt import QtGui
from cytoflowgui.workflow import Workflow
from traitsui.api import View, UI
from pyface.action.api import ToolBarManager
from envisage.api import Application
from pyface.tasks.action.api import TaskAction
from cytoflowgui.op_plugins.i_op_plugin import OP_PLUGIN_EXT


@provides(IDockPane)
class WorkflowDockPane(DockPane):
    
    id = 'edu.mit.synbio.workflow_pane'
    name = "Workflow"
    
    # the workflow this pane is displaying
    model = Instance(Workflow)
    
    # the UI object associated with the TraitsUI view
    ui = Instance(UI)
    
    # the application instance from which to get plugin instances
    application = Instance(Application)
    
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
         
        op_plugins = self.application.get_extensions(OP_PLUGIN_EXT)
                 
        for plugin in op_plugins:
            task_action = TaskAction(name=plugin.short_name,
                                     on_perform = lambda: self.add_workflow_item(plugin))
            self.toolbar.append(task_action)
             
        window = QtGui.QMainWindow()
        window.addToolBar(self.toolbar.create_tool_bar(window))
         
        self.ui = self.model.edit_traits(kind='subpanel', parent=window)
        window.setCentralWidget(self.ui.control)
         
        window.setParent(parent)
        parent.setWidget(window)
         
        return window
    
    def add_workflow_item(self, plugin):
        self.task.add_operation(plugin, after = self.model.selected)
    
    ### TODO - rebuild/refresh when self.view is changed.
    def _workflow_changed(self):
        pass   
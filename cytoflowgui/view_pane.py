from traits.api import Instance, Any, List, on_trait_change, Str, Dict, Bool
from traitsui.api import UI, View, Item, EnumEditor
from pyface.tasks.api import DockPane, Task
from pyface.action.api import ToolBarManager
from pyface.tasks.action.api import TaskAction
from pyface.qt import QtGui, QtCore
from cytoflowgui.view_plugins import IViewPlugin
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.workflow import Workflow

class ViewDockPane(DockPane):
    """
    A DockPane to manipulate the traits of the currently selected view.
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.view_traits_pane'
    name = 'View Properties'

    # the Task that serves as the controller
    task = Instance(Task)

    # the IViewPlugins that the user can possibly choose.  set by the controller
    # as we're instantiated
    view_plugins = List(IViewPlugin)
    
    # changed depending on whether the selected wi in the model is valid.
    # would use a direct listener, but valid gets changed outside
    # the UI thread and we can't change UI things from other threads.
    enabled = Bool
    
    # the UI object associated with the object we're editing.
    # NOTE: we don't maintain a reference to the IView itself...
    _ui = Instance(UI)
    
    _current_view_id = Str
    
    # the layout that manages the pane
    _layout = Instance(QtGui.QVBoxLayout)
    
    # the main panel control
    _control = Instance(QtGui.QWidget)
    
    # the entire window (plus toolbar)
    _window = Instance(QtGui.QMainWindow)
    
    # actions associated with views
    _actions = Dict(Str, TaskAction)
    
    # the default action
    _default_action = Instance(TaskAction)
    
    ###########################################################################
    # 'ITaskPane' interface.
    ###########################################################################

    def create(self, *args, **kwargs):
        super(ViewDockPane, self).create(*args, **kwargs)       
        self.on_trait_change(self._set_enabled, 'enabled', dispatch = 'ui')

    def destroy(self):
        """ 
        Destroy the toolkit-specific control that represents the pane.
        """
        # Destroy the Traits-generated control inside the dock control.
        if self._ui is not None:
            self._ui.dispose()
            self._ui = None

        # Destroy the dock control.
        super(ViewDockPane, self).destroy()

    ###########################################################################
    # 'IDockPane' interface.
    ###########################################################################

    def create_contents(self, parent):
        """ 
        Create and return the toolkit-specific contents of the dock pane.
        """
        
        self.toolbar = ToolBarManager(orientation = 'vertical',
                                      show_tool_names = False,
                                      image_size = (32, 32))
        
        self._default_action = TaskAction(name = "Default\nView",
                                          on_perform = lambda: self.task.set_current_view("default"),
                                          style = 'toggle',
                                          visible = False)
        self._actions["default"] = self._default_action
        self.toolbar.append(self._default_action)
        
        for plugin in self.plugins:
            task_action = TaskAction(name = plugin.short_name,
                                     on_perform = lambda id=plugin.view_id:
                                                    self.task.set_current_view(id),
                                     image = plugin.get_icon(),
                                     style = 'toggle')
            self._actions[plugin.view_id] = task_action
            self.toolbar.append(task_action)
            
        self._window = QtGui.QMainWindow()
        tb = self.toolbar.create_tool_bar(self._window)
        self._window.addToolBar(QtCore.Qt.RightToolBarArea, tb)
   
        # the top-level control 
        scroll_area = QtGui.QScrollArea()
        scroll_area.setFrameShape(QtGui.QFrame.NoFrame)
        scroll_area.setWidgetResizable(True)
   
        # the panel that we can scroll around
        self._control = QtGui.QWidget()
    
        # the panel's layout manager
        self._layout = QtGui.QVBoxLayout()
        self._control.setLayout(self._layout)
        scroll_area.setWidget(self._control)
        
        self._window.setCentralWidget(scroll_area)
        self._window.setParent(parent)
        parent.setWidget(self._window)
        self._window.setEnabled(False)
        return self._window
            
#     @on_trait_change('_current_view_id')
#     def _picker_current_view_changed(self, obj, name, old, new):
#         if new:
#             self.task.set_current_view(new)
        
    def _set_enabled(self, obj, name, old, new):
        self._window.setEnabled(new)
            
    @on_trait_change('task:model:selected.valid')
    def _on_model_valid_changed(self, obj, name, old, new):
#        print "valid changed: {0}".format(threading.current_thread())
        
        if not new:
            return
        
        if name == 'selected':
            new = new.valid
                
        # redirect to the UI thread
        self.enabled = True if new == "valid" else False

    @on_trait_change('task:model:selected.current_view')
    def _model_current_view_changed(self, obj, name, old, new):
        # at the moment, this only gets called from the UI thread, so we can
        # do UI things.   we get notified if *either* the currently selected 
        # workflowitem *or* the current view changes.
        
         # untoggle everything on the toolbar
        for action in self._actions.itervalues():
            action.checked = False
  
        if name == 'selected':
            old = old.current_view if old else None
            new = new.current_view if new else None

        
        if old:
            # remove the view's widget from the layout
            self._layout.takeAt(self._layout.indexOf(self._ui.control))
            
            # and the spacer
            self._layout.takeAt(self._layout.count() - 1)
            
            self._ui.control.setParent(None)
            self._ui.dispose()
            
        if new:
            if new == self.task.model.selected.default_view:
                self._default_action.checked = True
            else:
                self._actions[new.id].checked = True
            
            self._ui = new.handler.edit_traits(kind='subpanel', 
                                               parent=self._control)              
            self._layout.addWidget(self._ui.control)
            self._layout.addStretch(stretch = 1)
            self._current_view_id = new.id
        else:
            self._current_view_id = ""

    @on_trait_change('task:model:selected.default_view')
    def _default_view_changed(self, obj, name, old, new):
        old_view = (old.default_view 
                    if isinstance(obj, Workflow) 
                       and isinstance(old, WorkflowItem) 
                    else old)
          
        new_view = (new.default_view 
                    if isinstance(obj, Workflow) 
                       and isinstance(new, WorkflowItem)
                    else new)
        
        if new_view is None:
            self._default_action.visible = False
        else:
            plugins = [x for x in self.task.op_plugins 
                       if x.operation_id == self.task.model.selected.operation.id]
            plugin = plugins[0]
            self._default_action.image = plugin.get_icon()
            self._default_action.visible = True
                         
#         if old_view is not None:
#             old_id = old_view.id
#             del self._plugins_dict[old_id]
#              
#         if new_view is not None:
#             new_id = new_view.id
#             new_name = "{0} (Default)".format(new_view.friendly_id)
#             self._plugins_dict[new_id] = new_name
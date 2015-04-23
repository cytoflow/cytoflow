from traits.api import Instance, Any, List, on_trait_change, Property, Str, Dict
from traitsui.api import UI, View, Item, EnumEditor, Handler
from cytoflow.views.i_view import IView
from pyface.tasks.api import DockPane, Task
from pyface.qt import QtGui
from envisage.api import Application, Plugin
from cytoflowgui.view_plugins import IViewPlugin, VIEW_PLUGIN_EXT
from cytoflowgui.workflow_item import WorkflowItem
from cytoflowgui.workflow import Workflow
from scipy.weave.build_tools import old_argv

class ViewDockPane(DockPane):
    """
    A DockPane to manipulate the traits of the currently selected view.
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.view_traits_pane'
    name = 'View Properties'

    # the Task that serves as the controller
    task = Instance('flow_task.FlowTask')

    # the IViewPlugins that the user can possibly choose.  set by the controller
    # as we're instantiated
    plugins = List(IViewPlugin)
    
    # the UI object associated with the object we're editing.
    # NOTE: we don't maintain a reference to the IView itself...
    _ui = Instance(UI)

    # plugin name --> plugin ID
    _plugins_dict = Dict(Str, Str)
    
    _current_view_id = Property
    
    # the layout that manages the pane
    _layout = Instance(QtGui.QVBoxLayout)
    
    # the parent of the layout
    _parent = Any
    
    ###########################################################################
    # 'ITaskPane' interface.
    ###########################################################################

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

        self._plugins_dict = {p.view_id: p.short_name for p in self.plugins}
        plugin_chooser = View(Item('_current_view_id',
                                   editor=EnumEditor(name = "_plugins_dict"),
                                   show_label = False))
        
        picker_control = self.edit_traits(kind='subpanel',
                                          view = plugin_chooser).control
   
        # the top-level control 
        control = QtGui.QScrollArea()
        control.setFrameShape(QtGui.QFrame.NoFrame)
        control.setWidgetResizable(True)
   
        # the panel that we can scroll around
        panel = QtGui.QWidget()
    
        # the panel's layout manager
        self._layout = QtGui.QVBoxLayout()
        self._layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        panel.setLayout(self._layout)
        control.setWidget(panel)
        
        # add the selector to the layout
        self._layout.addWidget(picker_control)
        
        # and a separator
        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        self._layout.addWidget(line)
        
        self._parent = parent
        
        self._parent.setEnabled(False)
        
        return control
            
    # magic: gets the _current_view_id Property value
    def _get__current_view_id(self):
        if self.task.model.selected and self.task.model.selected.current_view:
            return self.task.model.selected.current_view.id
        else:
            return ""
    
    def _set__current_view_id(self, view_id):
        self.task.set_current_view(view_id)
            
    @on_trait_change('task:model:selected.valid')
    def _workflow_valid_changed(self, obj, name, old, new):
        if not new:
            return
        
        if name == 'selected':
            new = new.valid
                
        if new == "valid":
            self._parent.setEnabled(True)
        else:
            self._parent.setEnabled(False)

    @on_trait_change('task:model:selected.current_view')
    def _current_view_changed(self, obj, name, old, new):
        
        # we get notified if *either* the currently selected workflowitem
        # *or* the current view changes.
  
        if name == 'selected':
            old = old.current_view if old else None
            new = new.current_view if new else None
        
        if old:
            self._layout.takeAt(self._layout.indexOf(self._ui.control))
            self._ui.dispose()
            self._ui = None
            
        if new:
            # note: the "handler" attribute isn't defined on IView; it's dynamically
            # associated with these instances in flow_task.FlowTask.set_
            self._ui = new.handler.edit_traits(kind='subpanel', 
                                                parent=self._parent)              
            self._layout.addWidget(self._ui.control)
        
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
                        
        if old_view is not None:
            old_id = old_view.id
            del self._plugins_dict[old_id]
             
        if new_view is not None:
            new_id = new_view.id
            new_name = "{0} (Default)".format(new_view.friendly_id)
            self._plugins_dict[new_id] = new_name
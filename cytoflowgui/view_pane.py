from traits.api import Instance, Any, List, on_trait_change, Property, Str, Dict
from traitsui.api import UI, View, Item, EnumEditor, Handler
from cytoflow.views.i_view import IView
from pyface.tasks.api import DockPane, Task
from pyface.qt import QtGui
from envisage.api import Application, Plugin
from cytoflowgui.view_plugins import IViewPlugin, VIEW_PLUGIN_EXT

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
    
    # the IView we're currently editing.  set by the controller; then
    # we display the view controls
    view = Instance(IView) 
    
    # if the IOperation whose results we're viewing has a default view
    # (for example, an interactive widget), keep a ref; otherwise, None
    default_view = Instance(IView)
    
    # the UI object associated with the object we're editing.
    # NOTE: we don't maintain a reference to the IView itself...
    _ui = Instance(UI)

    # plugin name --> plugin ID
    _plugins_dict = Dict(Str, Str)

    # the id for the IView we're currently showing
    _current_plugin = Str
    
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
        plugin_view = View(Item('_current_plugin',
                                editor=EnumEditor(values=self._plugins_dict),
                                show_label = False))
        
        picker_control = self.edit_traits(kind='subpanel',
                                          view = plugin_view).control
   
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
        return control

    @on_trait_change('_current_plugin')
    def _on_current_plugin_changed(self, obj, name, old, new):
        self.task.set_current_view(self, new)
        
    @on_trait_change('default_view')
    def _on_default_view_changed(self, obj, name, old, new):

        if isinstance(old, IView):
            del self._plugins_dict[old.view_id]
            #old_name = "Default: {0}".format(old.short_name)
            
        new_name = "Default: {0}".format(new.short_name)
        self._plugins_dict[new.view_id] = new_name
        
    @on_trait_change('view')
    def _view_changed(self, obj, name, old, new):
        
        if isinstance(old, IView):
            self._layout.takeAt(self._layout.count() - 1) 
            self._ui = None
            
        if not isinstance(new, IView):
            self._current_plugin = None
            return 
        
        self._current_plugin = new.id
    
        # note: the "handler" attribute isn't defined on IView; it's dynamically
        # associated with these instances in flow_task.FlowTask.set_current_view
        
        self._ui = new.handler.edit_traits(kind='subpanel', 
                                           parent=self._parent)
                 
        self._layout.addWidget(self._ui.control)

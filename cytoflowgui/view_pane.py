from traits.api import Instance, Any, on_trait_change
from traitsui.api import UI, View, Item, EnumEditor
from cytoflow.views.i_view import IView
from pyface.tasks.api import DockPane, Task
from pyface.qt import QtGui
from cytoflowgui.workflow import Workflow
from envisage.api import Application, Plugin
from cytoflowgui.view_plugins import IViewPlugin, VIEW_PLUGIN_EXT

class ViewDockPane(DockPane):
    """
    A DockPane to manipulate the traits of the currently selected view.
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.view_traits_pane'
    name = 'View Properties'

    # the plugin instance for the IView we're currently showing
    current_plugin = Instance(IViewPlugin)
    
    # the cytoflow visualizer whose traits we're showing
    view = Instance(IView)
    
    # the layout that manages the pane
    layout = Instance(QtGui.QVBoxLayout)
    
    # the parent of the layout
    parent = Any
    
    # the UI object associated with the TraitsUI view
    ui = Instance(UI)
    
    # the application instance from which to get plugin instances
    application = Instance(Application)
    
    # the Task that serves as the controller
    task = Instance(Task)
    
    # the main model instance
    model = Instance(Workflow)
    
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
        super(ViewDockPane, self).destroy()

    ###########################################################################
    # 'IDockPane' interface.
    ###########################################################################

    def create_contents(self, parent):
        """ 
        Create and return the toolkit-specific contents of the dock pane.
        """

        plugins = self.application.get_extensions(VIEW_PLUGIN_EXT)
        plugins_dict = {p: p.name for p in plugins}
        plugin_view = View(Item('current_plugin',
                                editor=EnumEditor(values=plugins_dict),
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
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        panel.setLayout(self.layout)
        control.setWidget(panel)
        
        # add the selector to the layout
        self.layout.addWidget(picker_control)
        
        # and a separator
        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        self.layout.addWidget(line)
        
        self.parent = parent
        return control


    @on_trait_change('current_plugin')
    def _plugin(self, old, new):
        if isinstance(old, Plugin):
            self.layout.takeAt(self.layout.count() - 1)
            
        self.view = new.get_view()
        traitsui_view = new.get_traitsui_view(self.view)
        
        self.ui = self.view.edit_traits(kind='subpanel', 
                                        parent=self.parent,
                                        view=traitsui_view)
        
        self.layout.addWidget(self.ui.control)

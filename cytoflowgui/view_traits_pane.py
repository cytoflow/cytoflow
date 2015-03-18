from traits.api import HasTraits, Instance
from traitsui.api import UI, View, Item, Group
from cytoflow.views.i_view import IView
from pyface.tasks.api import DockPane, Task
from pyface.qt import QtGui
from cytoflowgui.workflow import Workflow
from envisage.api import Application

class ViewTraitsDockPane(DockPane):
    """
    A DockPane to manipulate the traits of the currently selected view.
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.view_traits_pane'
    name = 'View Properties'

    # the cytoflow visualizer whose traits we're showing
    view = Instance(IView)

    # the UI object associated with the TraitsUI view
    ui = Instance(UI)
    
    # the application instance from which to get plugin instances
    application = Instance(Application)
    
    # the Task that serves as the controller
    task = Instance(Task)
    
    # an empty view
    empty_view = View()
    
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
        super(ViewTraitsDockPane, self).destroy()

    ###########################################################################
    # 'IDockPane' interface.
    ###########################################################################

    def create_contents(self, parent):
        """ Create and return the toolkit-specific contents of the dock pane.
        """
        if self.view is not None:
            self.ui = self.view.edit_traits(kind='subpanel', parent=parent)
            return self.ui.control
        else:
            self.ui = self.edit_traits(kind='subpanel', parent=parent, view='empty_view')
            return self.ui.control
    
    ### TODO - rebuild/refresh when self.view is changed.
    def _view_changed(self):
        pass
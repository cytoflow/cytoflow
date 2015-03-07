from traits.api import Instance
from traitsui.api import UI
from cytoflow.views.i_view import IView
from pyface.tasks.dock_pane import DockPane

class ViewTraitsDockPane(DockPane):
    """
    A DockPane to manipulate the traits of the currently selected view.
    """

    #### TaskPane interface ###############################################

    id = 'edu.mit.synbio.view_traits_pane'
    name = 'View Properties'

    # the cytoflow visualizer whose traits we're showing
    view = Instance(IView)

    # the UI object associated with the Traits view
    ui = Instance(UI)
    
    ###########################################################################
    # 'ITaskPane' interface.
    ###########################################################################

    def destroy(self):
        """ 
        Destroy the toolkit-specific control that represents the pane.
        """
        # Destroy the Traits-generated control inside the dock control.
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
        self.ui = self.view.edit_traits(kind='subpanel', parent=parent)
        return self.ui.control
    
    ### TODO - rebuild/refresh when self.view is changed.
    def _view_changed(self):
        pass
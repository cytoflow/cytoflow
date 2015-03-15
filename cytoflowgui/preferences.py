from envisage.ui.tasks.api import PreferencesPane, TaskFactory
from apptools.preferences.api import PreferencesHelper
from traits.api import Bool, Dict, Enum, List, Str, Unicode
from traitsui.api import EnumEditor, HGroup, VGroup, Item, Label, \
    View

class CytoflowPreferences(PreferencesHelper):
    """ 
    The preferences helper for the Cytoflow application.
    """

    #### 'PreferencesHelper' interface ########################################

    # The path to the preference node that contains the preferences.
    preferences_path = 'edu.mit.synbio.cytoflow.preferences'

    #### Preferences ##########################################################

    # The task to activate on app startup if not restoring an old layout.
    default_task = Str

    # Whether to always apply the default application-level layout.
    # See TasksApplication for more information.
    always_use_default_layout = Bool


class CytoflowPreferencesPane(PreferencesPane):
    """ 
    The preferences pane for the Cytoflow application.
    """

    #### 'PreferencesPane' interface ##########################################

    # The factory to use for creating the preferences model object.
    model_factory = CytoflowPreferences

    #### 'AttractorsPreferencesPane' interface ################################

    task_map = Dict(Str, Unicode)

    view = View(
        VGroup(HGroup(Item('always_use_default_layout'),
                      Label('Always use the default active task on startup'),
                      show_labels = False),
               HGroup(Label('Default active task:'),
                      Item('default_task',
                           editor=EnumEditor(name='handler.task_map')),
                      enabled_when = 'always_use_default_layout',
                      show_labels = False),
               label='Application startup'),
        resizable=True)

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _task_map_default(self):
        return dict((factory.id, factory.name)
                    for factory in self.dialog.application.task_factories)
#!/usr/bin/env python2.7
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from envisage.ui.tasks.api import PreferencesPane
from apptools.preferences.api import PreferencesHelper
from traits.api import Bool, Dict, Str, Unicode
from traitsui.api import EnumEditor, HGroup, VGroup, Item, Label, View

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
#!/usr/bin/env python3.8
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2018
# (c) Brian Teague 2018-2021
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
from traits.api import Bool
from traitsui.api import HGroup, VGroup, Item, Label, View

class CytoflowPreferences(PreferencesHelper):
    """ 
    The preferences helper for the Cytoflow application.
    """

    #### 'PreferencesHelper' interface ########################################

    # The path to the preference node that contains the preferences.
    preferences_path = 'edu.mit.synbio.cytoflow.preferences'

    #### Preferences ##########################################################

    # Whether to always apply the default application layout.
    # See TasksApplication for more information.
    always_use_default_layout = Bool


class CytoflowPreferencesPane(PreferencesPane):
    """ 
    The preferences pane for the Cytoflow application.
    """

    #### 'PreferencesPane' interface ##########################################

    # The factory to use for creating the preferences model object.
    model_factory = CytoflowPreferences

    view = View(
        VGroup(HGroup(Item('always_use_default_layout'),
                      Label('Always use the default layout on startup?'),
                      show_labels = False),
               label='Application startup'),
        resizable=True)


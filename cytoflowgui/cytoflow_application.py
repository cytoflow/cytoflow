#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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

'''
Created on Mar 15, 2015

@author: brian
'''
from __future__ import absolute_import

from future import standard_library
standard_library.install_aliases()
import sys, logging, io
from cytoflowgui import multiprocess_logging

from envisage.ui.tasks.api import TasksApplication
from pyface.api import error
from pyface.tasks.api import TaskWindowLayout
from traits.api import Bool, Instance, List, Property, Str

from .preferences import CytoflowPreferences
  
def gui_handler_callback(msg, app):
    app.application_error = msg

class CytoflowApplication(TasksApplication):
    """ The cytoflow Tasks application.
    """

    # The application's globally unique identifier.
    id = 'edu.mit.synbio.cytoflow'

    # The application's user-visible name.
    name = 'Cytoflow'

    # Override two traits from TasksApplication so we can provide defaults, below

    # The default window-level layout for the application.
    default_layout = List(TaskWindowLayout)

    # Whether to restore the previous application-level layout when the
    # applicaton is started.
    always_use_default_layout = Property(Bool)

    # are we debugging? at the moment, just for sending logs to the console
    debug = Bool

    # if there's an ERROR-level log message, drop it here     
    application_error = Str
    
    # keep the application log in memory
    application_log = Instance(io.StringIO, ())
            
    def run(self):

        ##### set up logging
        logging.getLogger().setLevel(logging.DEBUG)
        
        ## send the log to STDERR
        try:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
            logging.getLogger().addHandler(console_handler)
        except:
            # if there's no console, this fails
            pass
          
        ## capture log in memory
        mem_handler = logging.StreamHandler(self.application_log)
        mem_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
        logging.getLogger().addHandler(mem_handler)
         
        ## and display gui messages for exceprions
        gui_handler = multiprocess_logging.CallbackHandler( lambda msg, app = self: gui_handler_callback(msg, app))
        gui_handler.setLevel(logging.ERROR)
        logging.getLogger().addHandler(gui_handler)
         
        # must redirect to the gui thread
        self.on_trait_change(self.show_error, 'application_error', dispatch = 'ui')
        
        # run the GUI
        super(CytoflowApplication, self).run()
        
    def show_error(self, error_string):
        error(None, "An exception has occurred.  Please report a problem from the Help menu!\n\n"
                    "Afterwards, may need to restart Cytoflow to continue working.\n\n" 
                    + error_string)

    #### 'AttractorsApplication' interface ####################################

    preferences_helper = Instance(CytoflowPreferences)

    ###########################################################################
    # Private interface.
    ###########################################################################
    
    #### Trait initializers ###################################################

    def _default_layout_default(self):
        active_task = self.preferences_helper.default_task
        tasks = [ factory.id for factory in self.task_factories ]
        return [ TaskWindowLayout(*tasks,
                                  active_task = active_task,
                                  size = (800, 600)) ]

    def _preferences_helper_default(self):
        return CytoflowPreferences(preferences = self.preferences)

    #### Trait property getter/setters ########################################

    def _get_always_use_default_layout(self):
        return self.preferences_helper.always_use_default_layout

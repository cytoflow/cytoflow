#!/usr/bin/env python2.7

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

'''
Created on Mar 15, 2015

@author: brian
'''

import sys, logging, StringIO, traceback, threading
from cytoflowgui import multiprocess_logging

from envisage.ui.tasks.api import TasksApplication
from pyface.api import error
from pyface.tasks.api import TaskWindowLayout
from traits.api import Bool, Instance, List, Property, push_exception_handler, Str

from preferences import CytoflowPreferences

# pipe connections for communicating between processes
# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
# this = sys.modules[__name__]
# this.parent_conn = None
# this.child_conn = None

#  
# def gui_handler_callback(msg, app):
#     app.application_error = msg

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
#     
#     application_error = Str
#     application_log = Instance(StringIO.StringIO, ())
            
    def run(self):
        
#         # setup the root logger
#         h = multiprocess_logging.QueueHandler(log_q)  # Just the one handler needed
#         logging.getLogger().addHandler(h)
#         logging.getLogger().setLevel(logging.DEBUG)
#         
#         ## send the log to STDERR
#         console_handler = logging.StreamHandler()
#         console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
#          
#         ## capture log in memory
#         mem_handler = logging.StreamHandler(self.application_log)
#         mem_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
#         
#         ## and display gui messages for exceprions
#         gui_handler = multiprocess_logging.CallbackHandler( lambda msg, app = self: gui_handler_callback(msg, app))
#         gui_handler.setLevel(logging.ERROR)
#         
#         # start the queue listener to process log records from all processes
#         log_listener = multiprocess_logging.QueueListener(log_q, console_handler, mem_handler, gui_handler)
#         log_listener.start()
#         
#         # must redirect to the gui thread
#         self.on_trait_change(self.show_error, 'application_error', dispatch = 'ui')
        
        # run the GUI
        super(CytoflowApplication, self).run()
        
#         log_listener.stop()
        
    def show_error(self, error_string):
        error(None, "An exception has occurred.  Please report a problem from the Help menu!\n\n" 
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

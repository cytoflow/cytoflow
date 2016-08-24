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

import sys, threading, logging, multiprocessing

from traceback import format_exception_only, format_tb

from envisage.ui.tasks.api import TasksApplication
from pyface.api import error
from pyface.tasks.api import TaskWindowLayout
from traits.api import Bool, Instance, List, Property, push_exception_handler, Str

from preferences import CytoflowPreferences

from StringIO import StringIO

# pipe connections for communicating between processes
# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
this = sys.modules[__name__]
this.parent_conn = None
this.child_conn = None

def gui_notification_handler(obj, trait_name, old_value, new_value, app):
    
    (exc_type, exc_value, tb) = sys.exc_info()
    err_string = format_exception_only(exc_type, exc_value)[0]
    err_loc = format_tb(tb)[-1]
    err_ctx = threading.current_thread().name
    
    app.application_error = "Error: {0}\nLocation: {1}\nThread: {2}" \
                            .format(err_string, err_loc, err_ctx)
    

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
    
    application_error = Str
    
    application_log = Instance(StringIO, ())
        
    def run(self):
        ## set up the root logger
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        
        # set the multiprocessing logger to propogate messages
        multiprocessing.get_logger().propagate = True

        ## send the log to STDERR
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
        logger.addHandler(console_handler)
        
        ## capture the local log
        mem_handler = logging.StreamHandler(self.application_log)
        mem_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
        logger.addHandler(mem_handler)
        
        # install a global (gui) error handler for traits notifications
        push_exception_handler(handler = lambda obj, trait, old, new, app = self: \
                                            gui_notification_handler(obj, trait, old, new, app),
                               reraise_exceptions = True, 
                               main = True)
        
        # must redirect to the gui thread
        self.on_trait_change(self.show_error, 'application_error', dispatch = 'ui')
        
        # run the GUI
        super(CytoflowApplication, self).run()
        
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

#!/usr/bin/env python3.4
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

'''
Created on Mar 15, 2015

@author: brian
'''

import logging, io, os, pickle

from traits.api import Bool, Instance, List, Property, Str, Any, File

from envisage.ui.tasks.api import TasksApplication
from envisage.ui.tasks.tasks_application import TasksApplicationState

from pyface.api import error, ImageResource
from pyface.tasks.api import TaskWindowLayout
from pyface.qt import QtGui

from matplotlib.figure import Figure

from .workflow import LocalWorkflow
from .utility import CallbackHandler
from .preferences import CytoflowPreferences
from .matplotlib_backend_local import FigureCanvasQTAggLocal

logger = logging.getLogger(__name__)
  
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

    # did we get a filename on the command line?
    filename = File

    # if there's an ERROR-level log message, drop it here     
    application_error = Str
    
    # keep the application log in memory
    application_log = Instance(io.StringIO, ())

    # the model that's shared across all three tasks
    model = Instance(LocalWorkflow)

    # the connection to the remote process
    remote_process = Any
    remote_workflow_connection = Any
    remote_canvas_connection = Any
    
    # the matplotlib canvas that's shared across all three tasks
    canvas = Instance(FigureCanvasQTAggLocal)
            
    def run(self):

        # set the root logger level to DEBUG; decide what to do with each 
        # message on a handler-by-handler basis
        logging.getLogger().setLevel(logging.DEBUG)
        
        ## send the log to STDERR
        try:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
            console_handler.setLevel(logging.DEBUG if self.debug else logging.ERROR)
            logging.getLogger().addHandler(console_handler)
        except:
            # if there's no console, this fails
            pass
          
        ## capture log in memory
        mem_handler = logging.StreamHandler(self.application_log)
        mem_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
        mem_handler.setLevel(logging.DEBUG)
        logging.getLogger().addHandler(mem_handler)
         
        ## and display gui messages for exceptions
        gui_handler = CallbackHandler(lambda rec, app = self: gui_handler_callback(rec.getMessage(), app))
        gui_handler.setLevel(logging.ERROR)
        logging.getLogger().addHandler(gui_handler)
         
        # must redirect to the gui thread
        self.on_trait_change(self.show_error, 'application_error', dispatch = 'ui')
                
        # set up the model
        self.model = LocalWorkflow(self.remote_workflow_connection,
                                   debug = self.debug)
        
        # and the local canvas
        self.canvas = FigureCanvasQTAggLocal(Figure(), 
                                             self.remote_canvas_connection, 
                                             ImageResource('gear').create_image(size = (1000, 1000)))
    
        self.canvas.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding) 

        # run the GUI
        super(CytoflowApplication, self).run()
        
    def show_error(self, error_string):
        error(None, "An exception has occurred.  Please report a problem from the Help menu!\n\n"
                    "Afterwards, may need to restart Cytoflow to continue working.\n\n" 
                    + error_string)
        
    def stop(self):
        super().stop()
        self.model.shutdown_remote_process(self.remote_process)
        

    preferences_helper = Instance(CytoflowPreferences)

    ###########################################################################
    # Private interface.
    ###########################################################################
     
    def _load_state(self):
        """ 
        Loads saved application state, if possible.  Overload the envisage-
        defined one to fix a py3k bug and increment the TasksApplicationState
        version.
         
        """
        state = TasksApplicationState(version = 2)
        filename = os.path.join(self.state_location, 'application_memento')
        if os.path.exists(filename):
            # Attempt to unpickle the saved application state.
            try:
                with open(filename, 'rb') as f:
                    restored_state = pickle.load(f)
                if state.version == restored_state.version:
                    state = restored_state
                     
                    # make sure the active task is the main window
                    state.previous_window_layouts[0].active_task = 'edu.mit.synbio.cytoflowgui.flow_task'
                else:
                    logger.warn('Discarding outdated application layout')
            except:
                # If anything goes wrong, log the error and continue.
                logger.exception('Had a problem restoring application layout from %s',
                                 filename)
                  
        self._state = state
     
    def _save_state(self):
        """
        Saves the application window size, position, panel locations, etc
        """

        # Grab the current window layouts.
        window_layouts = [w.get_window_layout() for w in self.windows]
        self._state.previous_window_layouts = window_layouts
     
        # Attempt to pickle the application state.
        filename = os.path.join(self.state_location, 'application_memento')
        try:
            with open(filename, 'wb') as f:
                pickle.dump(self._state, f)
        except Exception as e:
            # If anything goes wrong, log the error and continue.
            logger.exception('Had a problem saving application layout: {}'.format(str(e)))
    #### Trait initializers ###################################################

    def _default_layout_default(self):
        active_task = self.preferences_helper.default_task
        tasks = [ factory.id for factory in self.task_factories ]
        return [ TaskWindowLayout(*tasks,
                                  active_task = active_task,
                                  size = (1280, 800)) ]

    def _preferences_helper_default(self):
        return CytoflowPreferences(preferences = self.preferences)

    #### Trait property getter/setters ########################################
 
    def _get_always_use_default_layout(self):
        return self.preferences_helper.always_use_default_layout

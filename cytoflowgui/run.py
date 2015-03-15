"""
Created on Feb 11, 2015

@author: brian
"""

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import logging

from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_plugin import TasksPlugin

from flow_task import FlowTaskPlugin
from cytoflow_application import CytoflowApplication

def run_gui(argv):
    
    logging.basicConfig(level=logging.DEBUG)

    plugins = [CorePlugin(), TasksPlugin(), FlowTaskPlugin()]
    app = CytoflowApplication(plugins = plugins)
    app.run()
    
    logging.shutdown()

if __name__ == '__main__':
    import sys
    run_gui(sys.argv)

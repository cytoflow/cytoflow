"""
Created on Feb 11, 2015

@author: brian
"""

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

from pyface.api import GUI
from pyface.tasks.api import TaskWindow
from flow_task import FlowTask

if __name__ == '__main__':
    gui = GUI()
    
    # create a Task and add it to a TaskWindow
    task = FlowTask()
    window = TaskWindow(size=(800, 600))
    window.add_task(task)
    
    window.open()
    
    gui.start_event_loop()